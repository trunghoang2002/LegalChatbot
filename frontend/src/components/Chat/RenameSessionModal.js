import React, { useState, useEffect } from 'react';
import Modal from 'react-modal';
import './Chat.css';

Modal.setAppElement('#root');

const RenameSessionModal = ({ isOpen, onRequestClose, onSubmit, session }) => {
  const [sessionName, setSessionName] = useState('');

  useEffect(() => {
    if (session) {
      setSessionName(session.name);
    }
  }, [session]);

  const handleSubmit = () => {
    onSubmit(sessionName);
    setSessionName('');
    onRequestClose();
  };

  return (
    <Modal
        isOpen={isOpen}
        onRequestClose={onRequestClose}
        contentLabel="Rename this session"
        className="chat-session-modal"
        overlayClassName="custom-modal-overlay"
    >
        <h2>Rename this session</h2>
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

export default RenameSessionModal;