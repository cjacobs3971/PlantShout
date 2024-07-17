import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const LoginRegister = () => {
  const [isLogin, setIsLogin] = useState(true);
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();
    const email = event.target.email.value;
    const password = event.target.password.value;

    const baseURL = 'http://127.0.0.1:5000';

    if (isLogin) {
      try {
        const response = await axios.post(`${baseURL}/api/login`, { email, password });
        if (response.status === 200) {
          localStorage.setItem('token', response.data.token);
          localStorage.setItem("user_id", response.data.user_id);
          navigate('/main'); // Navigate to main page on successful login
        } else {
          alert(response.data.message);
        }
      } catch (error) {
        console.error('Error logging in:', error);
        alert('Failed to login');
      }
    } else {
      try {
        const response = await axios.post(`${baseURL}/api/register`, { email, password });
        if (response.status === 201) {
          const loginResponse = await axios.post(`${baseURL}/api/login`, { email, password });
        if (loginResponse.status === 200) {
          localStorage.setItem('token', loginResponse.data.token);
          localStorage.setItem('user_id', loginResponse.data.user_id); // Store user_id
          navigate("/main");
        } // Switch to login view after successful registration
        } else {
          alert(response.data.message);
        }
      } catch (error) {
        console.error('Error registering:', error.response ? error.response.data : error);
        alert('Failed to register');
      }
    }
  };

  return (
    <div className="login-register">
      <form onSubmit={handleSubmit}>
        <h2>{isLogin ? 'Login' : 'Register'}</h2>
        <input type="email" name="email" placeholder="Email" required />
        <input type="password" name="password" placeholder="Password" required />
        {!isLogin && <input type="password" name="confirmPassword" placeholder="Confirm Password" required />}
        <button type="submit">{isLogin ? 'Login' : 'Register'}</button>
        <p onClick={() => setIsLogin(!isLogin)}>
          {isLogin ? "Don't have an account? Register" : 'Already have an account? Login'}
        </p>
      </form>
    </div>
  );
};

export default LoginRegister;

