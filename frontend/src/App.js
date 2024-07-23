import React from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import LoginRegister from './components/LoginRegister';
import MainPage from './components/MainPage';

const App = () => {
  const isAuthenticated = () => {
    return localStorage.getItem('token') !== null;
  };

  return (
    <Router>
      <Routes>
        <Route path="/login" element={isAuthenticated() ? <Navigate to = "/main" /> : <LoginRegister />} />
        <Route path="/main" element={isAuthenticated() ? <MainPage /> : <Navigate to="/login" />} />
        <Route path="/" element={<Navigate to={isAuthenticated() ? "/main" : "/login"} />} />
      </Routes>
    </Router>
  );
};

export default App;


