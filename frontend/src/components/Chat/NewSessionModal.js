import React, { useState } from 'react';
import Modal from 'react-modal';
import './Chat.css';

Modal.setAppElement('#root');

const CustomModal = ({ isOpen, onRequestClose, onSubmit }) => {
  const [sessionName, setSessionName] = useState('');

  const handleSubmit = () => {
    onSubmit(sessionName);
    setSessionName('');
    onRequestClose();
  };

  return (
    <Modal
        isOpen={isOpen}
        onRequestClose={onRequestClose}
        contentLabel="Enter Session Name"
        className="chat-session-modal"
        overlayClassName="custom-modal-overlay"
    >
        <h2>Enter session name</h2>
        <input
            type="text"
            value={sessionName}
            onChange={(e) => setSessionName(e.target.value)}
            placeholder="Session Name"
        />
        <div className="modal-button-div">
            <button onClick={handleSubmit}>Submit</button>
            <button onClick={onRequestClose}>Cancel</button>
        </div>
    </Modal>
  );
};

export default CustomModal;