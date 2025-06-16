import { BrowserRouter as Router, Route, Routes, useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import SignIn from './components/SignIn';
import SignUp from './components/SignUp';
import Chat from './components/Chat/Chat';

function App() {
  const navigate = useNavigate();

  const checkTokenExpiration = (token) => {
    try {
      const tokenData = JSON.parse(atob(token.split('.')[1]));
      const expirationTime = tokenData.exp * 1000; // Convert to milliseconds
      return Date.now() >= expirationTime;
    } catch (error) {
      return true; // If token is invalid, consider it expired
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      if (checkTokenExpiration(token)) {
        // Token is expired
        localStorage.removeItem('token');
        navigate('/signin');
      } else {
        navigate('/chat');
      }
    }
  }, [navigate]);

  return (
    <Routes>
      <Route path="/signin" element={<SignIn/>} />
      <Route path="/signup" element={<SignUp/>} />
      <Route path="/chat" element={<Chat/>} />
      <Route path="/" element={<SignIn/>} /> {/* Default route */}
    </Routes>
  );
}

function AppWrapper() {
  return (
    <Router>
      <App />
    </Router>
  );
}

export default AppWrapper;