import React from 'react';
import Modal from 'react-modal';
import './Chat.css';

Modal.setAppElement('#root');

const DeleteSessionModal = ({ isOpen, onRequestClose, onDelete, session }) => {
  const handleDelete = () => {
    onDelete(session);
    onRequestClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onRequestClose={onRequestClose}
      contentLabel="Delete this session"
      className="chat-session-modal"
      overlayClassName="custom-modal-overlay"
    >
      <h2>Delete this session</h2>
      <p>Are you sure you want to delete session "{session?.name}"?</p>
      <div className="modal-button-div">
        <button onClick={handleDelete}>Delete</button>
        <button onClick={onRequestClose}>Cancel</button>
      </div>
    </Modal>
  );
};

export default DeleteSessionModal;