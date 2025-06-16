import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { IoSend } from "react-icons/io5";
import { CiLogout } from "react-icons/ci";
import { FaUser, FaRobot } from "react-icons/fa";
import { FaMagnifyingGlass } from "react-icons/fa6";
import { RiMenu3Fill } from "react-icons/ri";
import ChatMessage from './ChatMessage';
import ChatSession from './ChatSession';
import NewSessionModal from './NewSessionModal';
import RenameSessionModal from './RenameSessionModal';
import DeleteSessionModal from './DeleteSessionModal';
import ChatSourcesModal from './ChatSourcesModal';
import './Chat.css';
import { useNavigate } from 'react-router-dom';
import { API_URLS } from '../../config';

const sleep = (ms) => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

function Chat() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [input, setInput] = useState('');
  const [chatLog, setChatLog] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [isNewSessionModalOpen, setIsNewSessionModalOpen] = useState(false);
  const [isRenameSessionModalOpen, setIsRenameSessionModalOpen] = useState(false);
  const [isDeleteSessionModalOpen, setIsDeleteSessionModalOpen] = useState(false);
  const [isChatSourcesModalOpen, setIsChatSourcesModalOpen] = useState(false);
  const [sessionToRename, setSessionToRename] = useState(null);
  const [sessionToDelete, setSessionToDelete] = useState(null);
  const [userEmail, setUserEmail] = useState('');
  const [username, setUsername] = useState('');
  const [showEmailDropdown, setShowEmailDropdown] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const token = localStorage.getItem('token');
  const textareaRef = useRef(null);

  useEffect(() => {
    // axios.get('http://localhost:5000/api/sessions', {
    axios.get(API_URLS.SESSIONS, {
      headers: { Authorization: `Bearer ${token}` }
    }).then(response => {
      setSessions(response.data);
    }).catch(error => {
      console.error('Error fetching chat sessions:', error.response?.data || error.message);
    });

    // axios.get('http://localhost:5000/api/profile', {
    axios.get(API_URLS.PROFILE, {
      headers: { Authorization: `Bearer ${token}` }
    }).then(response => {
      setUserEmail(response.data.email);
      setUsername(response.data.username);
    }).catch(error => {
      console.error('Error fetching user profile:', error.response?.data || error.message);
    });
  }, [token]);

  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      // Reset height to auto to get the correct scrollHeight
      textarea.style.height = 'auto';
      
      // Set new height based on scrollHeight
      const newHeight = Math.min(textarea.scrollHeight, 200); // Giới hạn chiều cao tối đa
      textarea.style.height = `${newHeight}px`;
    }
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [input]);

  const handleKeyDown = (e) => {
    if (e.shiftKey && e.key === 'Enter') {
      e.preventDefault();
      setInput(`${input}\n`);
    }
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleSessionChange = (session) => {
    setCurrentSession(session);
    // axios.get(`http://localhost:5000/api/history/${session.id}`, {
    axios.get(API_URLS.HISTORY(session.id), {
      headers: { Authorization: `Bearer ${token}` }
    }).then(response => {
      setChatLog(response.data);
    }).catch(error => {
      console.error('Error fetching chat history:', error);
    });
  };

  const handleNewSession = async (sessionName) => {
    setIsNewSessionModalOpen(true);
    if (window.innerWidth <= 768) {
      setIsSidebarOpen(false); // Đóng sidebar trên mobile
    }
    if (sessionName) {
      try {
        // const response = await axios.post('http://localhost:5000/api/sessions', { name: sessionName }, {
        const response = await axios.post(API_URLS.SESSIONS, { name: sessionName }, {
          headers: { Authorization: `Bearer ${token}` }
        });
        const newSession = response.data;
        setSessions([...sessions, newSession]);
        window.location.reload();
      } catch (error) {
        console.error('Error creating new session:', error);
      }
    }
  };

  const handleRenameSession = (session) => {
    setSessionToRename(session);
    setIsRenameSessionModalOpen(true);
  };

  const submitRenameSession = async (newName) => {
    if (newName && newName !== sessionToRename.name) {
      try {
        // const response = await axios.put(`http://localhost:5000/api/sessions/${sessionToRename.id}`, { name: newName }, {
        const response = await axios.put(API_URLS.SESSION(sessionToRename.id), { name: newName }, {
          headers: { Authorization: `Bearer ${token}` }
        });
        const updatedSession = response.data;
        setSessions(sessions.map(s => s.id === sessionToRename.id ? updatedSession : s));
        if (currentSession.id === sessionToRename.id) {
          setCurrentSession(updatedSession);
        }
        setIsRenameSessionModalOpen(false);
        setSessionToRename(null);
      } catch (error) {
        console.error('Error renaming session:', error);
      }
    }
  };

  const handleDeleteSession = (session) => {
    setSessionToDelete(session);
    setIsDeleteSessionModalOpen(true);
  };

  const confirmDeleteSession = async (session) => {
    try {
      // await axios.delete(`http://localhost:5000/api/sessions/${session.id}`, {
      await axios.delete(API_URLS.SESSION(session.id), {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSessions(sessions.filter(s => s.id !== session.id));
      if (currentSession.id === session.id) {
        setCurrentSession(null);
        setChatLog([]);
      }
      setIsDeleteSessionModalOpen(false);
      setSessionToDelete(null);
    } catch (error) {
      console.error('Error deleting session:', error);
    }
  };

  // const handleSubmit = async (e) => {
  //   e.preventDefault();
  //   if (input && currentSession) {
  //     const newMessage = { id: Date.now(), role: 'user', content: input };
  //     const updatedChatLog = [...chatLog, newMessage];
  //     setChatLog(updatedChatLog);
  //     setInput('');

  //     try {
  //       setIsLoading(true);
  //       const response = await axios.post('http://localhost:5000/api/chat', { session_id: currentSession.id, messages: updatedChatLog }, {
  //         headers: { Authorization: `Bearer ${token}` }
  //       });

  //       const aiMessage = { id: Date.now(), role: 'AI', content: response.data.response };
  //       setChatLog((prevChatLog) => [...prevChatLog, aiMessage]);
  //       setIsLoading(false);
  //     } catch (error) {
  //       console.error('Fetch error:', error);
  //       setIsLoading(false);
  //     }
  //   }
  // };
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (input && currentSession) {
      const newMessage = { id: Date.now(), role: 'user', content: input };
      const updatedChatLog = [...chatLog, newMessage];
      setChatLog(updatedChatLog);
      setInput('');

      try {
        setIsLoading(true);
        // Create a temporary message for processing steps
        const processingMessage = { id: Date.now(), role: 'AI', content: 'Đang xử lý...' };
        setChatLog(prevChatLog => [...prevChatLog, processingMessage]);

        // const response = await fetch(`http://localhost:5000/api/chat-stream`, {
        const response = await fetch(API_URLS.CHAT_STREAM, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            session_id: currentSession.id,
            messages: updatedChatLog,
          }),
        });

        if (!response.ok || !response.body) {
          throw new Error("Stream failed");
        }
  
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
  
        let fullResponse = '';
        let isFirstChunk = true;
  
        let buffer = ""; // lưu phần còn lại từ chunk trước
        let aiMessage = { ...processingMessage, content: "" };
  
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
  
          const chunk = decoder.decode(value, { stream: true });

          buffer += chunk;
  
          // Nếu server gửi kiểu SSE:
          // chunk = "data: {\"type\":\"response\", \"content\":\"...\"}\n\n"

          // Tách các sự kiện hoàn chỉnh (SSE phân tách bởi "\n\n")
          const lines = buffer.split("\n\n");

          // Giữ lại phần cuối nếu nó có thể là event chưa hoàn chỉnh
          buffer = lines.pop() || "";

          for (let line of lines) {
            if (!line.startsWith("data:")) continue;
  
            const payload = JSON.parse(line.slice(5).trim());
  
            if (payload.type === 'step') {
              if (payload.node === 'classify_question') {
                aiMessage.content = `Đang phân loại câu hỏi...`;
              } else if (payload.node === 'retrieve') {
                aiMessage.content = `Đang truy xuất tài liệu...`;
              } else if (payload.node === 'grade_documents') {
                aiMessage.content = `Đang đánh giá tài liệu...`;
              } else if (payload.node === 'generate') {
                aiMessage.content = `Đang tạo câu trả lời...`;
              } else if (payload.node === 'transform_query') {
                aiMessage.content = `Đang chuyển đổi câu hỏi...`;
              } else if (payload.node === 'grade_generation') {
                aiMessage.content = `Đang đánh giá câu trả lời...`;
              } else if (payload.node === 'update_memory') {
                aiMessage.content = `Đang cập nhật bộ nhớ...`;
              } else if (payload.node === 'max_retries') {
                aiMessage.content = `Đang xử lý...`;
              }
            } else if (payload.type === 'response') {
              if (isFirstChunk) {
                aiMessage.content = payload.content;
                fullResponse = payload.content;
                isFirstChunk = false;
              } else {
                aiMessage.content += payload.content;
                fullResponse += payload.content;
              }
            } else if (payload.type === 'done') {
              reader.cancel(); // hoặc break;
            }
  
            // Cập nhật chat log sau mỗi bước
            setChatLog(prev => {
              const newLog = [...prev];
              newLog[newLog.length - 1] = { ...aiMessage };
              return newLog;
            });
          }
        }

        // Xử lý phần còn lại của buffer nếu có
        if (buffer.trim()) {
          const lastLine = buffer.trim();
          if (lastLine.startsWith("data:")) {
            const payload = JSON.parse(lastLine.slice(5).trim());
            if (payload.type === 'response') {
              aiMessage.content += payload.content;
              fullResponse += payload.content;
              setChatLog(prev => {
                const newLog = [...prev];
                newLog[newLog.length - 1] = { ...aiMessage };
                return newLog;
              });
            }
          }
        }

        reader.releaseLock();
        setIsLoading(false);


      } catch (error) {
        console.error('Stream error:', error);
        setIsLoading(false);
        // Show error message
        setChatLog(prevChatLog => {
          const newLog = [...prevChatLog];
          const lastMessage = newLog[newLog.length - 1];
          if (lastMessage.role === 'AI') {
            lastMessage.content = 'Có lỗi xảy ra khi xử lý yêu cầu của bạn.';
          }
          return newLog;
        });
      }
    }
  };

  const handleLogOut = () => {
    localStorage.removeItem('token');
    navigate('/signin');
  }

  const handleClickBackGround = () => {
    setIsNewSessionModalOpen(false);
    setIsRenameSessionModalOpen(false);
    setIsDeleteSessionModalOpen(false);
    setIsChatSourcesModalOpen(false);
  }

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  const handleClickOutside = (e) => {
    if (window.innerWidth <= 768 && isSidebarOpen && !e.target.closest('.sidemenu') && !e.target.closest('.menu-toggle')) {
      setIsSidebarOpen(false);
    }
  };

  useEffect(() => {
    document.addEventListener('click', handleClickOutside);
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, [isSidebarOpen]);

  return (
    <div className="chat-container">
      <button className="menu-toggle" onClick={toggleSidebar}>
        <RiMenu3Fill />
      </button>
      <div className={`sidemenu ${isSidebarOpen ? 'open' : ''}`} onClick={(e) => {
        if (window.innerWidth <= 768 && isSidebarOpen && !e.target.closest('.chat-session-options') && !e.target.closest('.chat-session-options-active')) {
          setIsSidebarOpen(false);
        }
      }}>
        <div className="sidemenu-button" role="button" onClick={handleNewSession}>
          <span>+</span> New chat
        </div>
        <div className="session-list">
          {[...sessions].reverse().map((session) => (
            <ChatSession 
              key={session.id} 
              session={session} 
              onClick={() => handleSessionChange(session)} 
              isActive={currentSession?.id === session.id} 
              onRename={handleRenameSession}
              onDelete={handleDeleteSession}
            />
          ))}
        </div>
        <div className="logout-button" role="button" onClick={handleLogOut}>
          <CiLogout className="logout-button-icon"/>
          <div className="logout-button-text">Log out</div>
        </div>
      </div>
      <div className="chat-header">
        <div 
          className="chat-header-user" 
          onClick={() => setShowEmailDropdown(!showEmailDropdown)}
          style={{ cursor: 'pointer', position: 'relative' }}
        >
          <span>{username}</span>
          <div className="chat-avatar">
            <FaUser className='icon'/>
          </div>
          {showEmailDropdown && (
            <div 
              className="email-dropdown"
              style={{
                position: 'absolute',
                top: '100%',
                right: '0',
                backgroundColor: 'white',
                padding: '8px 12px',
                borderRadius: '4px',
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                zIndex: 1000,
                marginTop: '4px'
              }}
            >
              {userEmail}
            </div>
          )}
        </div>
      </div>
      <div className="chat">
        <div className="chat-log">
          {chatLog.map((message) => (
            <ChatMessage key={message.id} 
            message={message} 
            />
          ))}
        </div>
        <div className="chat-input-div">
          <form className="input-form" onSubmit={handleSubmit}>
            <textarea
              ref={textareaRef}
              className="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message here..."
              rows="1"
            />
            <div className="button-group">
              <button type="button" className="search-button" onClick={() => setIsChatSourcesModalOpen(true)}>
                <FaMagnifyingGlass />
              </button>
              <button type="submit" className="send-button" disabled={isLoading}>
                <IoSend />
              </button>
            </div>
          </form>
        </div>
      </div>
      <NewSessionModal
        isOpen={isNewSessionModalOpen}
        onRequestClose={() => setIsNewSessionModalOpen(false)}
        onSubmit={handleNewSession}
      />
      <RenameSessionModal
        isOpen={isRenameSessionModalOpen}
        onRequestClose={() => setIsRenameSessionModalOpen(false)}
        onSubmit={submitRenameSession}
        session={sessionToRename}
      />
      <DeleteSessionModal
        isOpen={isDeleteSessionModalOpen}
        onRequestClose={() => setIsDeleteSessionModalOpen(false)}
        onDelete={confirmDeleteSession}
        session={sessionToDelete}
      />
      <ChatSourcesModal
        isOpen={isChatSourcesModalOpen}
        onRequestClose={() => setIsChatSourcesModalOpen(false)}
        message={chatLog[chatLog.length - 1]}
        />
    </div>
  );
}

export default Chat;