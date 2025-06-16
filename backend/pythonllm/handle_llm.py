from typing import Literal, List
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

def get_llm(gemini_model_name: str, vllm_model_name: str, gemini_api_keys: List[str],  vllm_base_url: str = "", temperature: float = 0, top_p: float = 0.95, top_k: int = 10, max_output_tokens: int = 1000):
    llm_list = []
    for api_key in gemini_api_keys:
        llm_list.append(ChatGoogleGenerativeAI(
            model=gemini_model_name,
            google_api_key=api_key,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_output_tokens=max_output_tokens,
        ))
    if vllm_base_url:
        llm_list.append(ChatOpenAI(
            model=vllm_model_name,
            base_url=vllm_base_url,
            api_key="EMPTY",
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_output_tokens,
        ))
    if len(llm_list) > 1:
        llm = llm_list[0].with_fallbacks(llm_list[1:])
    else:
        llm = llm_list[0]
    return llm

# Data model for classification
class LegalClassification(BaseModel):
    """Phân loại câu hỏi pháp lý theo 7 loại."""

    loai: Literal["1", "2", "3", "4", "5", "6", "7"] = Field(
        ..., description="Loại của câu hỏi, là số từ 1 đến 7."
    )
    # do_tin_cay: int = Field(
    #     ..., description="Độ tin cậy của phân loại, giá trị từ 0 đến 100."
    # )
    # ly_do: str = Field(
    #     ..., description="Giải thích ngắn gọn lý do phân loại."
    # )

def get_legal_question_classifier(gemini_model_name: str, vllm_model_name: str, gemini_api_keys: List[str],  vllm_base_url: str = ""):
    llm = get_llm(gemini_model_name, vllm_model_name, gemini_api_keys, vllm_base_url)
    structured_legal_classifier = llm.with_structured_output(LegalClassification)
    # Prompt
    system_prompt = """Bạn là một chuyên gia pháp lý có nhiệm vụ phân loại câu hỏi theo lĩnh vực pháp luật. 
Hãy đọc kỹ câu hỏi bên dưới và xác định nó thuộc một trong các loại sau:

Loại 1: Không phải câu hỏi pháp lý
Loại 2: Câu hỏi về Hiến pháp
Loại 3: Câu hỏi thuộc một trong các luật sau:
  - Luật Lao động
  - Luật An toàn vệ sinh lao động
  - Luật Bảo hiểm xã hội
  - Luật Công đoàn
  - Luật Việc làm
Loại 4: Câu hỏi thuộc một trong các luật sau:
  - Luật Dân sự
  - Luật Hôn nhân và gia đình
  - Luật Bảo vệ quyền lợi người tiêu dùng
Loại 5: Câu hỏi thuộc Luật Hình sự
Loại 6: Câu hỏi liên quan đến nhiều hơn một loại trong các loại từ 2 đến 5
Loại 7: Là câu hỏi pháp lý nhưng không thuộc bất kỳ bộ luật nào kể trên"""
    classification_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{question}"),
    ])

    # Pipeline
    legal_question_classifier = classification_prompt | structured_legal_classifier
    return legal_question_classifier

# Data model for document grading
class GradeDocuments(BaseModel):
    """Đánh giá tài liệu truy xuất có liên quan đến câu hỏi pháp luật hay không (yes/no)."""

    binary_score: Literal["yes", "no"] = Field(description="Tài liệu có liên quan đến câu hỏi không, 'yes' hoặc 'no'")

def get_retrieval_grader(gemini_model_name: str, vllm_model_name: str, gemini_api_keys: List[str],  vllm_base_url: str = ""):
    llm = get_llm(gemini_model_name, vllm_model_name, gemini_api_keys, vllm_base_url)
    structured_llm_grader = llm.with_structured_output(GradeDocuments)
    # Prompt 
    system = """Bạn là một chuyên gia pháp luật, có nhiệm vụ đánh giá mức độ liên quan giữa một tài liệu truy xuất và ngữ cảnh hội thoại của người dùng. \n 
Nếu tài liệu chứa nội dung hoặc ý nghĩa liên quan đến chủ đề pháp lý đang được thảo luận trong cuộc hội thoại (không chỉ riêng câu hỏi hiện tại), hãy đánh giá là 'yes'. Nếu không liên quan, đánh giá là 'no'. \n
Đây không phải là kiểm tra nghiêm ngặt, mục tiêu là loại bỏ các tài liệu không đúng trọng tâm hoặc sai lệch về chủ đề. \n
Chỉ trả lời một từ duy nhất cho trường 'binary_score': 'yes' hoặc 'no'."""
    grade_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "Điều luật truy xuất:\n{document}\nLịch sử hội thoại (nếu có):\n{summary}\nCâu hỏi hiện tại:\n{question}"),
        ]
    )

    retrieval_grader = grade_prompt | structured_llm_grader
    return retrieval_grader

def get_question_rewriter(gemini_model_name: str, vllm_model_name: str, gemini_api_keys: List[str],  vllm_base_url: str = ""):
    llm = get_llm(gemini_model_name, vllm_model_name, gemini_api_keys, vllm_base_url)
    # Prompt 
    system = """Bạn là một chuyên gia pháp lý, có nhiệm vụ cải biên câu hỏi đầu vào để tối ưu hóa việc truy xuất thông tin trong kho dữ liệu văn bản pháp luật. \n 
Hãy đọc kỹ câu hỏi và viết lại nó sao cho rõ ràng hơn, mang tính pháp lý chính xác hơn, thể hiện đúng mục đích và bản chất pháp lý của người dùng. \n
Nếu câu hỏi không đủ nghĩa, có thể dựa trên lịch sử hội thoại trước đó để bổ sung ý.
Chỉ trả lại câu hỏi đã được viết lại, không thêm bất kỳ nội dung nào khác."""
    re_write_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "Lịch sử hội thoại (nếu có):\n{summary}\nCâu hỏi ban đầu: \n\n {question} \n Hãy viết lại câu hỏi một cách tối ưu hơn."),
        ]
    )

    question_rewriter = re_write_prompt | llm | StrOutputParser()
    return question_rewriter

class SafeStrOutputParser(StrOutputParser):
    def invoke(self, input, config, **kwargs):
        try:
            return super().invoke(input, config, **kwargs)
        except Exception as e:
            # Nếu bị cắt, cố lấy phần content nếu có
            if hasattr(e, "llm_output") and e.llm_output:
                content = e.llm_output.get("content", "")
                print("[DEBUG] Truncated output:", content[:100])  # Log 100 ký tự đầu
                return content
            # raise e

def get_rag_chain(gemini_model_name: str, vllm_model_name: str, gemini_api_keys: List[str],  vllm_base_url: str = ""):
    llm = get_llm(gemini_model_name, vllm_model_name, gemini_api_keys, vllm_base_url, 0.3, 0.9, 10, 1500)
    # Prompt
    system = """Bạn là trợ lý pháp lý AI chuyên về pháp luật Việt Nam. Nhiệm vụ của bạn là phân tích câu hỏi của người dùng và các điều luật được cung cấp để đưa ra câu trả lời chính xác, rõ ràng, kèm tham chiếu pháp lý cụ thể.

Hướng dẫn xử lý:
1. Đọc kỹ câu hỏi người dùng và xác định vấn đề pháp lý cốt lõi mà người dùng muốn hỏi.
2. Phân tích các điều luật được cung cấp trong phần "Điều luật truy xuất" để tìm thông tin liên quan.
3. Trích dẫn rõ ràng số điều, khoản, tên văn bản luật và nội dung quan trọng (ví dụ: Điều 10 Bộ luật Dân sự 2015).
4. Dựa trên phân tích ở bước 2 đưa ra kết luận giải đáp vấn đề pháp lý người dùng đang hỏi.
5. Nếu không đủ cơ sở pháp lý để đưa ra kết luận, thông báo: "Hiện chưa đủ cơ sở pháp lý để trả lời."

Lưu ý:
-  Chỉ sử dụng điều luật được cung cấp, không bịa đặt, tự ý thêm thông tin bên ngoài.
-  Hãy đảm bảo rằng câu trả lời của bạn chi tiết, đầy đủ và chính xác.

Ví dụ:
Điều luật truy xuất:
Bộ luật Lao động 2019
Điều 35 Người lao động có quyền đơn phương chấm dứt hợp đồng lao động trong một số trường hợp...
Câu hỏi người dùng:
Người lao động có thể đơn phương chấm dứt hợp đồng lao động không?
Câu trả lời:
Theo Điều 35 Bộ luật Lao động 2019, người lao động có thể đơn phương chấm dứt hợp đồng nếu...
Trong câu hỏi, không thấy đề cập rõ thời gian báo trước. Tuy nhiên ...
Trong trường hợp này, người lao động có quyền đơn phương chấm dứt hợp đồng nếu đảm bảo điều kiện về thời gian báo trước theo quy định.
"""
    generate_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "\nTóm tắt lịch sử hội thoại trước đó (nếu có):\n{summary}\nLịch sử hội thoại gần nhất (nếu có):\n{chat_history}\nĐiều luật truy xuất:\n{document}\nCâu hỏi người dùng: {question}\nCâu trả lời:"),
        ]
    )
    # Chain
    safe_parser = SafeStrOutputParser()
    rag_chain = generate_prompt | llm | safe_parser
    return rag_chain

# Data model for hallucination detection
class GradeHallucinations(BaseModel):
    """Đánh giá câu trả lời của mô hình có dựa trên tài liệu được truy xuất hay không."""

    binary_score: Literal["yes", "no"] = Field(description="Câu trả lời có dựa vào tài liệu được cung cấp không, 'yes' hoặc 'no'")

def get_hallucination_grader(gemini_model_name: str, vllm_model_name: str, gemini_api_keys: List[str],  vllm_base_url: str = ""):
    llm = get_llm(gemini_model_name, vllm_model_name, gemini_api_keys, vllm_base_url)
    structured_llm_grader = llm.with_structured_output(GradeHallucinations)
    # Prompt 
    system = """Bạn là một chuyên gia pháp lý, có nhiệm vụ đánh giá xem câu trả lời của mô hình LLM có dựa vào nội dung trong các tài liệu pháp luật được truy xuất hay không. \n 
Nếu câu trả lời có nội dung phù hợp và được hỗ trợ bởi tài liệu đã truy xuất, hãy đánh giá là 'yes'. Nếu câu trả lời chứa thông tin không có trong tài liệu, hoặc không liên quan, hãy đánh giá là 'no'. \n
Chỉ trả lời một từ duy nhất cho trường 'binary_score': 'yes' hoặc 'no'."""
    hallucination_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "Tài liệu pháp luật được truy xuất: \n\n {documents} \n\n Câu trả lời của mô hình LLM: {generation}"),
        ]
    )

    hallucination_grader = hallucination_prompt | structured_llm_grader
    return hallucination_grader

# Data model for answer grading
class GradeAnswer(BaseModel):
    """Đánh giá câu trả lời có giải quyết đúng câu hỏi của người dùng hay không.."""

    binary_score: Literal["yes", "no"] = Field(description="Câu trả lời có giải quyết đúng câu hỏi không, 'yes' hoặc 'no'")

def get_answer_grader(gemini_model_name: str, vllm_model_name: str, gemini_api_keys: List[str],  vllm_base_url: str = ""):
    llm = get_llm(gemini_model_name, vllm_model_name, gemini_api_keys, vllm_base_url)
    structured_llm_grader = llm.with_structured_output(GradeAnswer)
    # Prompt 
    system = """Bạn là một chuyên gia pháp luật. Nhiệm vụ của bạn là đánh giá xem câu trả lời từ mô hình LLM có giải quyết đầy đủ và đúng trọng tâm câu hỏi pháp lý của người dùng hay không. \n 
Nếu câu trả lời trả lời đúng và hợp lý cho câu hỏi được đặt ra, đánh giá là 'yes'. Nếu câu trả lời không đúng trọng tâm, mơ hồ, hoặc không trả lời được câu hỏi, đánh giá là 'no'. \n
Chỉ trả lời một từ duy nhất cho trường 'binary_score': 'yes' hoặc 'no'"""
    answer_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "\nTóm tắt lịch sử hội thoại trước đó (nếu có):\n{summary}Câu hỏi người dùng: \n\n {question} \n\n Câu trả lời của mô hình LLM: {generation}"),
        ]
    )

    answer_grader = answer_prompt | structured_llm_grader
    return answer_grader

def get_summary_history(gemini_model_name: str, vllm_model_name: str, gemini_api_keys: List[str],  vllm_base_url: str = ""):
    llm = get_llm(gemini_model_name, vllm_model_name, gemini_api_keys, vllm_base_url, 0.3, 0.9, 10, 1000)
    # Prompt
    system = """Bạn là một hệ thống hỗ trợ pháp luật. Hãy đọc đoạn hội thoại giữa người dùng và AI dưới đây và tóm tắt lại nội dung chính đã được thảo luận. Tóm tắt cần ngắn gọn, rõ ràng và đầy đủ các điểm quan trọng.

Ví dụ: 
Lịch sử hội thoại: 
User: Nếu tôi gửi đơn nghỉ việc nhưng công ty không phản hồi thì tôi có được nghỉ không?
AI: Chào bạn, theo Bộ luật Lao động 2019, nếu bạn là người lao động làm việc theo hợp đồng không xác định thời hạn, bạn có quyền đơn phương chấm dứt hợp đồng mà không cần lý do, nhưng phải báo trước cho người sử dụng lao động ít nhất 45 ngày. Nếu hợp đồng có thời hạn thì thời gian báo trước là ít nhất 30 ngày. Trong trường hợp làm việc theo hợp đồng dưới 12 tháng, thời gian báo trước là ít nhất 3 ngày. Tuy nhiên, có một số trường hợp đặc biệt, bạn có thể nghỉ ngay không cần báo trước, ví dụ như bị ngược đãi, bị không được thanh toán lương đúng hạn, hoặc bị phân công công việc không đúng như hợp đồng đã ký.
Tóm tắt:
Người dùng hỏi về việc nếu đã gửi đơn xin nghỉ việc nhưng công ty không phản hồi thì có được nghỉ không? AI trả lời rằng người lao động vẫn có quyền nghỉ sau khi hết thời hạn báo trước theo quy định, kể cả khi công ty không phản hồi, miễn là đã gửi đơn nghỉ hợp lệ. Điều quan trọng là người lao động cần lưu lại bằng chứng đã gửi đơn như văn bản, email, hoặc xác nhận nhận đơn từ phía công ty để bảo vệ quyền lợi nếu có tranh chấp xảy ra.
Kết thúc ví dụ.
"""
    summary_prompt = ChatPromptTemplate.from_messages([
        ("system", system),
        ("human", "\nLịch sử hội thoại:\n{history}\nTóm tắt:")
    ])


    summary_history = summary_prompt | llm | StrOutputParser()
    return summary_history

# Data model for judge
class Judge(BaseModel):
    """Đánh giá câu trả lời của mô hình"""
    legal_factuality_score: Literal["1", "2", "3", "4", "5"] = Field(description="Đánh giá độ chính xác pháp lý của câu trả lời, từ 1 đến 5")
    reasoning_clarity_score: Literal["1", "2", "3", "4", "5"] = Field(description="Đánh giá tính hợp lý và dễ hiểu của câu trả lời, từ 1 đến 5")

def get_llm_as_a_judge(gemini_model_name: str, vllm_model_name: str, gemini_api_keys: List[str],  vllm_base_url: str = ""):
    llm = get_llm(gemini_model_name, vllm_model_name, gemini_api_keys, vllm_base_url, 0, 0.95, 10, 2000)
    structured_llm_judge = llm.with_structured_output(Judge)
    # Prompt
    system = """Bạn là một chuyên gia pháp lý có khả năng đánh giá chất lượng câu trả lời của một hệ thống AI tư vấn pháp luật.
Hãy thực hiện các bước sau:

### 1. **Đánh giá Độ chính xác pháp lý (Legal Factuality):**
- Câu trả lời có đúng với nội dung và tinh thần của tài liệu pháp luật đã cung cấp không?
- Có sai lệch, ngụy tạo hay diễn giải sai không?

→ Chấm điểm từ 1 đến 5 (1 là tệ nhất, 5 là tốt nhất)

### 2. **Đánh giá Tính hợp lý và dễ hiểu (Reasoning Clarity):**
- Câu trả lời có logic, mạch lạc không?
- Người không chuyên ngành luật có dễ hiểu không?

→ Chấm điểm từ 1 đến 5 (1 là tệ nhất, 5 là tốt nhất)

Chỉ trả lời một số nguyên cho trường 'legal_factuality_score' và 'reasoning_clarity_score' tương ứng với đánh giá của bạn. Không trả lời bất kỳ thông tin nào khác."""
    judge_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "\n\nCâu hỏi của người dùng:\n{question}\n\nTài liệu pháp luật liên quan mà hệ thống đã truy xuất được:\n{document}\n\nCâu trả lời của mô hình LLM:\n{generation}"),
        ]
    )
    judge_chain = judge_prompt | structured_llm_judge
    return judge_chain