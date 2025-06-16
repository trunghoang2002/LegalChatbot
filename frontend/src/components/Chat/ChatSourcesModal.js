import React from 'react';
import Modal from 'react-modal';
import './Chat.css';

Modal.setAppElement('#root');

const ChatSourcesModal = ({ isOpen, onRequestClose, message }) => {
    let response = message?.content;
    let sources = '';
    if (response?.includes("SOURCES OF INFORMATION:")) {
        sources = response?.split("SOURCES OF INFORMATION:").pop().trim();
    }

    if (sources == '') {
        sources = "No sources available";
    }
  
return (
    <Modal
        isOpen={isOpen}
        onRequestClose={onRequestClose}
        contentLabel="Sources of last message"
        className="chat-session-modal sources-modal"
        overlayClassName="custom-modal-overlay"
    >
        <h2>Sources of last message</h2>
        <div className='sources-message-box'>
            <p className='sources-message'>{sources}</p>
        </div>
        <div className="modal-button-div">
            <button onClick={onRequestClose}>Close</button>
        </div>
    </Modal>
);
};

export default ChatSourcesModal;