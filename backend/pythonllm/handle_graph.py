from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
import os
from typing import Dict, List, Any, Tuple
from qdrant_client.models import Distance
from sentence_transformers import SentenceTransformer
from typing_extensions import TypedDict
from langgraph.graph import START, END, StateGraph
from pprint import pprint

from handle_qdrant import get_qdrant_client, initialize_qdrant_collection
from handle_retriever import FusionRetriever, LawIndexRetriever
from handle_llm import get_legal_question_classifier, get_retrieval_grader, get_question_rewriter, get_rag_chain, get_hallucination_grader, get_answer_grader, get_summary_history

QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME")

VLLM_BASE_URL_1 = os.getenv("VLLM_BASE_URL_1")
VLLM_MODEL_NAME_1 = "AITeamVN/GRPO-VI-Qwen2-7B-RAG"

VLLM_BASE_URL_2 = os.getenv("VLLM_BASE_URL_2")
VLLM_MODEL_NAME_2 = "Qwen/Qwen2.5-7B-Instruct"

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_API_KEY_1 = os.getenv("GOOGLE_API_KEY_1")
GOOGLE_API_KEY_2 = os.getenv("GOOGLE_API_KEY_2")
GOOGLE_API_KEY_3 = os.getenv("GOOGLE_API_KEY_3")
GOOGLE_API_KEY_4 = os.getenv("GOOGLE_API_KEY_4")
GOOGLE_API_KEY_5 = os.getenv("GOOGLE_API_KEY_5")
GOOGLE_API_KEY_6 = os.getenv("GOOGLE_API_KEY_6")
# LIST_GOOGLE_API_KEY = [GOOGLE_API_KEY_1, GOOGLE_API_KEY_2, GOOGLE_API_KEY_3, GOOGLE_API_KEY_4, GOOGLE_API_KEY_5, GOOGLE_API_KEY_6]
LIST_GOOGLE_API_KEY = [GOOGLE_API_KEY]
GEMINI_MODEL_NAME = "gemini-2.0-flash"

# Get the absolute path of the project root directory
# PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Update paths to use absolute paths
EMBEDDINGS_MODEL_NAME_OR_PATH_1 = os.path.join(BACKEND_ROOT, "embedding/output_v1")
EMBEDDINGS_MODEL_NAME_OR_PATH_2 = os.path.join(BACKEND_ROOT, "embedding/output_v2")
VECTOR_NAME_1 = "vn-law-embedding_1"
VECTOR_NAME_2 = "vn-law-embedding_2"
VECTOR_SIZE = 128
VECTOR_DISTANCE = Distance.COSINE
MAX_RETRIES_COUNT = 3

# qdrant
client = get_qdrant_client(QDRANT_URL, QDRANT_API_KEY)
initialize_qdrant_collection(client, QDRANT_COLLECTION_NAME, VECTOR_NAME_1, VECTOR_NAME_2, VECTOR_SIZE, VECTOR_DISTANCE)

# retriever
embeddings_1 = SentenceTransformer(EMBEDDINGS_MODEL_NAME_OR_PATH_1, truncate_dim = 128)
embeddings_2 = SentenceTransformer(EMBEDDINGS_MODEL_NAME_OR_PATH_2, truncate_dim = 128)
fusion_retriever = FusionRetriever(
    client=client,
    embeddings_1=embeddings_1,
    embeddings_2=embeddings_2,
    collection_name=QDRANT_COLLECTION_NAME,
    vector_name_1=VECTOR_NAME_1,
    vector_name_2=VECTOR_NAME_2
)
index_retriever = LawIndexRetriever(
    doc_path=os.path.join(BACKEND_ROOT, "dataset/all_docs.json"),
    meta_path=os.path.join(BACKEND_ROOT, "dataset/all_doc_metas.json")
)
init_question = "Tội trộm cắp tài sản dưới 2 triệu đồng bị xử lý như thế nào?"
# Retrieval
fusion_retriever.invoke(init_question)
index_retriever.invoke(init_question)

# llm
hallucination_grader = get_hallucination_grader(
    gemini_model_name=GEMINI_MODEL_NAME,
    vllm_model_name=VLLM_MODEL_NAME_1,
    gemini_api_keys=LIST_GOOGLE_API_KEY,
    vllm_base_url=VLLM_BASE_URL_1,
)
answer_grader = get_answer_grader(
    gemini_model_name=GEMINI_MODEL_NAME,
    vllm_model_name=VLLM_MODEL_NAME_1,
    gemini_api_keys=LIST_GOOGLE_API_KEY,
    vllm_base_url=VLLM_BASE_URL_1,
)
summary_history = get_summary_history(
    gemini_model_name=GEMINI_MODEL_NAME,
    vllm_model_name=VLLM_MODEL_NAME_1,
    gemini_api_keys=LIST_GOOGLE_API_KEY,
    vllm_base_url=VLLM_BASE_URL_1,
)
legal_question_classifier = get_legal_question_classifier(
    gemini_model_name=GEMINI_MODEL_NAME,
    vllm_model_name=VLLM_MODEL_NAME_1,
    gemini_api_keys=LIST_GOOGLE_API_KEY,
    vllm_base_url=VLLM_BASE_URL_1,
)
retrieval_grader = get_retrieval_grader(
    gemini_model_name=GEMINI_MODEL_NAME,
    vllm_model_name=VLLM_MODEL_NAME_1,
    gemini_api_keys=LIST_GOOGLE_API_KEY,
    vllm_base_url=VLLM_BASE_URL_1,
)
question_rewriter = get_question_rewriter(
    gemini_model_name=GEMINI_MODEL_NAME,
    vllm_model_name=VLLM_MODEL_NAME_1,
    gemini_api_keys=LIST_GOOGLE_API_KEY,
    vllm_base_url=VLLM_BASE_URL_1,
)

rag_chain = get_rag_chain(
    gemini_model_name=GEMINI_MODEL_NAME,
    vllm_model_name=VLLM_MODEL_NAME_1,
    gemini_api_keys=LIST_GOOGLE_API_KEY,
    vllm_base_url=VLLM_BASE_URL_1,
)

class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: question
        generation: LLM generation
        documents: list of documents 
        chat_history: list of chat history tuples
        summary: list of summaries
        retry_generate_count: number of generation attempts
        need_grade_docs: boolean to check if need to grade documents
    """
    question : str
    generation : str
    documents : List[str]
    chat_history: List[Tuple[str, str]] # [(user, ai)]
    summary: List[str]
    retry_generate_count: int
    retry_transform_count: int
    node_start: List[str]
    this_node: List[Dict]
    need_grade_docs: bool
### Node ###

def retrieve(state):
    """
    Retrieve documents

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, documents, that contains retrieved documents
    """
    print("---RETRIEVE---")
    question = state["question"]

    # Retrieval
    documents_1 = index_retriever.invoke(question)
    documents_2 = fusion_retriever.invoke(question)
    documents = documents_1 + documents_2
    documents = [doc.page_content for doc in documents]
    print("documents: ")
    for doc in documents:
        print(doc)
        print("\n--------------------\n")
    return {"documents": documents, "question": question}

def generate(state):
    """
    Generate answer

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, generation, that contains LLM generation
    """
    print("---GENERATE---")
    question = state["question"]
    documents = state["documents"]
    summary = state.get("summary", [])
    retry_generate_count = state.get("retry_generate_count", 0) + 1
    if not summary:
        summary_text = ""
    else:
        summary_text = "\n".join(summary[-2:])
    chat_history = state.get("chat_history", [])
    if not chat_history:
        history_text = ""
    else:
        history_text = f"User: {chat_history[-1][0]}\nAI: {chat_history[-1][1]}"
    
    # RAG generation
    try:
        generation = rag_chain.invoke({"summary": summary_text, "chat_history": history_text, "document": documents, "question": question})
    except Exception as e:
        print(e)
        generation = "Rất tiếc, có lỗi xảy ra. Vui lòng thử lại sau."
    print("generation: ", generation)

    return {"documents": documents, "question": question, "generation": generation, "retry_generate_count": retry_generate_count}

def grade_documents(state):
    """
    Determines whether the retrieved documents are relevant to the question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates documents key with only filtered relevant documents
    """

    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    question = state["question"]
    documents = state["documents"]
    summary = state.get("summary", [])
    if not summary:
        summary_text = ""
    else:
        summary_text = summary[-1]
    
    # Score each doc
    filtered_docs = []
    for doc in documents:
        score = retrieval_grader.invoke({"summary": summary_text, "question": question, "document": doc})
        grade = score.binary_score
        if grade == "yes":
            print("---GRADE: DOCUMENT RELEVANT---")
            filtered_docs.append(doc)
        else:
            print("---GRADE: DOCUMENT NOT RELEVANT---")
            continue
    return {"documents": filtered_docs, "question": question}

def transform_query(state):
    """
    Transform the query to produce a better question.

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Updates question key with a re-phrased question
    """

    print("---TRANSFORM QUERY---")
    question = state["question"]
    documents = state["documents"]
    summary = state.get("summary", [])
    retry_transform_count = state.get("retry_transform_count", 0) + 1
    if not summary:
        summary_text = ""
    else:
        summary_text = summary[-1]

    # Re-write question
    try:
        better_question = question_rewriter.invoke({"summary": summary_text, "question": question})
    except Exception as e:
        print(e)
        better_question = question
    return {"documents": documents, "question": better_question, "retry_transform_count": retry_transform_count}

def classify_question(state):
    """
    Classify question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Next node to call
    """

    print("---CLASSIFY QUESTION---")
    question = state["question"]
    history_documents = state.get("documents", [])
    need_grade_docs = state.get("need_grade_docs", True)
    print("question: ", question)

    try:
        classification = legal_question_classifier.invoke({"question": question})   
    except Exception as e:
        print(e)
        generation = "Rất tiếc, có lỗi xảy ra. Vui lòng thử lại sau."
        return {"documents": [], "question": question, "generation": generation}
    
    if classification.loai == 1:
        generation = "Câu hỏi của bạn dường như không thuộc lĩnh vực pháp luật. Vui lòng đặt câu hỏi liên quan đến pháp luật để hệ thống có thể hỗ trợ chính xác hơn."
        return {"documents": [], "question": question, "generation": generation}
    elif classification.loai == 7:
        generation = f"Câu hỏi của bạn thuộc lĩnh vực pháp luật, tuy nhiên hiện tại hệ thống chưa hỗ trợ trả lời các câu hỏi thuộc lĩnh vực này. {classification.ly_do} Bạn có thể hỏi về các vấn đề như lao động, dân sự, hình sự, hiến pháp... để hệ thống hỗ trợ tốt hơn."
        return {"documents": [], "question": question, "generation": generation}
    else:
        documents = index_retriever.invoke(question)
        if documents:
            documents = [doc.page_content for doc in documents]
            print("documents: ")
            for doc in documents:
                print(doc)
                print("\n--------------------\n")
            need_grade_docs = False
        else:
            documents = history_documents
        return {"documents": documents, "question": question, "generation": "", "need_grade_docs": need_grade_docs}

def update_memory(state):
    """
    Cập nhật chat_history và summary sau mỗi lượt.
    """
    print("---UPDATE MEMORY---")
    chat_history = state.get("chat_history", [])
    summary = state.get("summary", [])
    question = state.get("question", "")
    generation = state.get("generation", "")

    if question and generation:
        # Thêm lượt chat mới
        chat_history.append((question, generation))

        # Tóm tắt
        chat_text = f"User: {question}\nAI: {generation}"
        summary.append(summary_history.invoke({"history": chat_text}))

    return {
        **state,
        "chat_history": chat_history,
        "summary": summary,
    }

def max_retries(state):
    """
    Max retries
    """
    question = state["question"]
    generation = "Rất tiếc, hệ thống hiện không tìm thấy thông tin phù hợp với câu hỏi của bạn. Vui lòng thử lại sau."
    return {"documents": [], "question": question, "generation": generation}

### Edges ###

def route_question(state):
    """
    Route to next node base on classification ressult
    Args:
        state (dict): The current graph state

    Returns:
        str: Decision for next node to call
    """
    print("ROUTE QUESION")
    question = state["question"]
    documents = state.get("documents", [])
    generation = state["generation"]
    need_grade_docs = state.get("need_grade_docs", True)

    if generation:
        print("---DECISION: END---")
        return "end"
    if documents and need_grade_docs:
        print("---DECISION: GRADE DOCUMENTS---")
        return "history docs"
    elif documents and not need_grade_docs:
        print("---DECISION: GENERATE---")
        return "generate"
    else:
        print("---DECISION: RETRIEVE---")
        return "no docs"

def decide_to_generate(state):
    """
    Determines whether to generate an answer, or re-generate a question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Binary decision for next node to call
    """

    print("---ASSESS GRADED DOCUMENTS---")
    question = state["question"]
    filtered_documents = state["documents"]
    retry_transform_count = state.get("retry_transform_count", 0)

    if not filtered_documents:
        # All documents have been filtered check_relevance
        # We will re-generate a new query
        print("---DECISION: ALL DOCUMENTS ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---")
        if retry_transform_count >= MAX_RETRIES_COUNT:
            print("---DECISION: MAX RETRIES TRANSFORM QUERY REACHED---")
            return "max retries"
        print("---DECISION: RE-TRY TRANSFORM QUERY---")
        return "not relevant"
    else:
        # We have relevant documents, so generate answer
        print("---DECISION: GENERATE---")
        return "relevant"

def grade_generation_v_documents_and_question(state):
    """
    Determines whether the generation is grounded in the document and answers question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Decision for next node to call
    """

    print("---CHECK HALLUCINATIONS---")
    if state.get("node_start"):
        state["node_start"].append("grade_generation")
    question = state["question"]
    documents = state["documents"]
    generation = state["generation"]
    summary = state.get("summary", [])
    retry_generate_count = state.get("retry_generate_count", 0)
    retry_transform_count = state.get("retry_transform_count", 0)
    if not summary:
        summary_text = ""
    else:
        summary_text = summary[-1]

    try:
        score = hallucination_grader.invoke({"documents": documents, "generation": generation})
        grade = score.binary_score
    except Exception as e:
        print(e)
        grade = "no"

    # Check hallucination
    if grade == "yes":
        print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
        # Check question-answering
        print("---GRADE GENERATION vs QUESTION---")
        try:
            score = answer_grader.invoke({"summary": summary_text, "question": question, "generation": generation})
            grade = score.binary_score
        except Exception as e:
            print(e)
            grade = "no"
        if grade == "yes":
            print("---DECISION: GENERATION ADDRESSES QUESTION---")
            return "useful"
        else:
            print("---DECISION: GENERATION DOES NOT ADDRESS QUESTION---")
            print("generation: ", generation)
            print("question: ", question)
            if retry_transform_count >= MAX_RETRIES_COUNT:
                if retry_generate_count < MAX_RETRIES_COUNT:
                    print("---DECISION: MAX RETRIES TRANSFORM QUERY REACHED, RE-TRY GENERATION---")
                    return "not supported"
                else:
                    print("---DECISION: MAX RETRIES TRANSFORM QUERY REACHED---")
                    return "max retries"
            print("---DECISION: RE-TRY TRANSFORM QUERY---")
            return "not useful"
    else:
        print("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS---")
        print("generation: ", generation)
        print("documents: ", documents)
        if retry_generate_count >= MAX_RETRIES_COUNT:
            print("---DECISION: MAX RETRIES GENERATION REACHED---")
            return "max retries"
        print("---DECISION: RE-TRY GENERATION---")
        return "not supported"

def node_wrapper(name, func):
    def wrapped(state):
        # Send node start information before processing
        if state.get("node_start"):
            state["node_start"].append(name)
            if name == "update_memory":
                state["this_node"].append(
                    {
                        "generation": state["generation"],
                        "documents": state["documents"]
                    }
                )
        # print(f">>> START executing node: {name}")
        return func(state)
    return wrapped

def build_graph(wrap_func=None):
    """
    Build the graph
    """
    workflow = StateGraph(GraphState)

    # Define the nodes
    if wrap_func:
        # workflow.add_node("web_search", web_search) # web search
        workflow.add_node("retrieve", wrap_func("retrieve", retrieve)) # retrieve
        workflow.add_node("classify_question", wrap_func("classify_question", classify_question)) # classify_question
        workflow.add_node("grade_documents", wrap_func("grade_documents", grade_documents)) # grade documents
        workflow.add_node("generate", wrap_func("generate", generate)) # generatae
        workflow.add_node("transform_query", wrap_func("transform_query", transform_query)) # transform_query
        workflow.add_node("update_memory", wrap_func("update_memory", update_memory))
        workflow.add_node("max_retries", wrap_func("max_retries", max_retries))
    else:
        # workflow.add_node("web_search", web_search) # web search
        workflow.add_node("retrieve", retrieve) # retrieve
        workflow.add_node("classify_question", classify_question) # classify_question
        workflow.add_node("grade_documents", grade_documents) # grade documents
        workflow.add_node("generate", generate) # generatae
        workflow.add_node("transform_query", transform_query) # transform_query
        workflow.add_node("update_memory", update_memory)
        workflow.add_node("max_retries", max_retries)

    # Build graph
    workflow.add_edge(START, "classify_question")
    workflow.add_conditional_edges(
        "classify_question",
        route_question,
        {
            "no docs": "retrieve",
            "history docs": "grade_documents",
            "generate": "generate",
            "end": END,
        },
    )
    # workflow.add_edge("web_search", "generate")
    workflow.add_edge("retrieve", "grade_documents")
    workflow.add_conditional_edges(
        "grade_documents",
        decide_to_generate,
        {
            "not relevant": "transform_query",
            "relevant": "generate",
            "max retries": "max_retries",
        },
    )
    workflow.add_edge("transform_query", "retrieve")
    workflow.add_conditional_edges(
        "generate",
        grade_generation_v_documents_and_question,
        {
            "not supported": "generate",
            "useful": "update_memory",
            "not useful": "transform_query",
            "max retries": "max_retries",
        },
    )
    workflow.add_edge("max_retries", END)
    workflow.add_edge("update_memory", END)

    # Compile
    app = workflow.compile()
    return app

def get_response(my_graph: StateGraph, new_question: str, last_state: dict = None):
    if last_state:
        last_state["question"] = new_question
        inputs = last_state
    else:
        inputs = {"question": new_question}
    print("inputs: ")
    pprint(inputs)
    for step in my_graph.stream(inputs):
        for node_name, state in step.items():
            # Node
            print(f"Node '{node_name}':")
            # Optional: print full state at each node
            pprint(state, indent=2, width=80, depth=None)
        print("\n---\n")
    # Final state
    return state

def visualize_graph(my_graph: StateGraph):
    image = my_graph.get_graph().draw_mermaid_png()
    with open("graph.png", "wb") as f:
        f.write(image)

my_graph = build_graph(node_wrapper)

if __name__ == "__main__":
    import time
    # question = "người lao động có thể đơn phương chấm dứt hợp đồng lao động không?"
    
    last_state = None
    while True:
        question = input("Enter a question or enter 'q' to quit: ")
        if question == "q":
            break
        start_time = time.time()
        current_state = get_response(my_graph, question, last_state)
        end_time = time.time()
        print(current_state["generation"])
        print(f"Time taken: {end_time - start_time} seconds")
        print("\n---\n")
        last_state = current_state

    # visualize_graph(my_graph)