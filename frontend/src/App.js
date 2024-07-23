import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import LoginRegister from './components/LoginRegister';
import MainPage from './components/MainPage';

const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(localStorage.getItem('token') !== null);

  useEffect(() => {
    const handleStorageChange = () => {
      setIsAuthenticated(localStorage.getItem('token') !== null);
    };

    window.addEventListener('storage', handleStorageChange);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
    };
  }, []);

  return (
    <Router>
      <Routes>
        <Route path="/login" element={isAuthenticated ? <Navigate to="/main" /> : <LoginRegister setIsAuthenticated={setIsAuthenticated} />} />
        <Route path="/main" element={isAuthenticated ? <MainPage setIsAuthenticated={setIsAuthenticated} /> : <Navigate to="/login" />} />
        <Route path="/" element={<Navigate to={isAuthenticated ? "/main" : "/login"} />} />
      </Routes>
    </Router>
  );
};

export default App;


