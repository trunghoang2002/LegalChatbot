import { useState, useEffect, useRef } from 'react';
import './Chat.css';
import { CiChat2 } from "react-icons/ci";
import { BsThreeDotsVertical } from "react-icons/bs";
import { FaRegTrashAlt } from "react-icons/fa";
import { LuPencil } from "react-icons/lu";

const ChatSession = ({ session, isActive, onClick, onRename, onDelete }) => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  const toggleDropdown = () => {
    setIsDropdownOpen(!isDropdownOpen);
  };

  const handleClickOutside = (event) => {
    if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
      setIsDropdownOpen(false);
    }
  };

  useEffect(() => {
    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    } else {
      document.removeEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isDropdownOpen]);

  return (
    <div className={`chat-session ${isActive ? 'chat-session-active' : ''}`} onClick={onClick}>
      <CiChat2 className={`chat-session-icon ${isActive ? 'chat-session-icon-active' : ''}`} />
      <div className={`chat-session-name ${isActive ? 'chat-session-name-active' : ''}`}>
        {session.name}
      </div>
      <BsThreeDotsVertical className={`chat-session-options ${isActive ? 'chat-session-options-active' : ''}`} onClick={toggleDropdown} />
      {isDropdownOpen && (
        <div className="dropdown-menu" ref={dropdownRef}>
          <div className="dropdown-item" onClick={() => onRename(session)}> <LuPencil className="drop-down-icon"/> Rename</div>
          <div className="dropdown-item" onClick={() => onDelete(session)}> <FaRegTrashAlt className="drop-down-icon"/> Delete</div>
        </div>
      )}
    </div>
  );
}

export default ChatSession;