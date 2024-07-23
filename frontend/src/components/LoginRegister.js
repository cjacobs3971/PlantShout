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

    const baseURL = 'https://plantshout-199a76bab95e.herokuapp.com';

    if (isLogin) {
      try {
        const response = await axios.post(`${baseURL}/api/login`, { email, password });
        if (response.status === 200) {
          localStorage.setItem('token', response.data.token);
          localStorage.setItem('user_id', response.data.user_id);
          console.log('Login successful, redirecting to main page'); // Debugging line
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
            localStorage.setItem('token', response.data.token);
            localStorage.setItem('user_id', response.data.user_id); // Store user_id
            console.log('Registration and login successful, redirecting to main page'); // Debugging line
            navigate('/main');
          
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
    <div className = "intro_text">
      <h1>PlantShout</h1>
      <h2>PlantShout is the dream help website for gardners and plant lovers. 
        Come here to not just get help from fellow plant lovers or AphidAI about issues your facing in the garden 
        but you can also provide valuable information for other people facing issues.
         </h2>
    </div>
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

