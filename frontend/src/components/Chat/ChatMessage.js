import { FaUser, FaRobot } from "react-icons/fa";
import './Chat.css';

const ChatMessage = ({ message }) => {
  const isAI = message.role === "AI";
  let response = message.content;
  // Cut out all of the part after SOURCES OF INFORMATION: in the response
  if (response.includes("\nSOURCES OF INFORMATION:")) {
    response = response.slice(0, response.indexOf("\nSOURCES OF INFORMATION:"));
  }
  else {
    response = response.trim();
  }
  // Cut out all the spaces and new line at the beginning of the response
  while (response.startsWith(" ") || response.startsWith("\n")) {
    response = response.slice(1);
  }
  return (
    <div className={`chat-message ${isAI ? "AI" : "user"}`}>
      <div className="chat-avatar">
        {isAI ? <FaRobot className="icon" /> : <FaUser className="icon" />}
      </div>
      <div className={`chat-content ${isAI ? "AI-chat" : "user-chat"}`}>
        {response}
      </div>
    </div>
  );
}

export default ChatMessage;