import React, { useState, useEffect } from 'react';
import axios from 'axios';
import AphidAI from '../images/AphidAI.png';
import { useNavigate } from 'react-router-dom';

const MainPage = ({ setIsAuthenticated }) => {
  const [posts, setPosts] = useState([]);
  const [category, setCategory] = useState('');
  const [tags, setTags] = useState('');
  const [title, setTitle] = useState('');
  const [text, setText] = useState('');
  const [image, setImage] = useState(null);
  const [commentText, setCommentText] = useState('');
  const [commentPostId, setCommentPostId] = useState(null);
  const navigate = useNavigate();

  const baseURL = 'https://plantshout-199a76bab95e.herokuapp.com';

  useEffect(() => {
    const fetchPosts = () => {
      axios.get(`${baseURL}/api/posts`)
        .then(response => setPosts(response.data))
        .catch(error => console.error('Error fetching posts:', error));
    };
  
    fetchPosts(); // Initial fetch
  
    const interval = setInterval(fetchPosts, 5000); // Fetch new posts every 5 seconds
  
    return () => clearInterval(interval); // Cleanup interval on component unmount
  }, []);
  

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
    navigate('/login');
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const formData = new FormData();
    formData.append('category', category);
    formData.append('tags', tags);
    formData.append('title', title);
    formData.append('text', text);
    formData.append('user_id', localStorage.getItem('user_id'));
    if (image) formData.append('image', image);

    const token = localStorage.getItem('token');
    const config = {
      headers: {
        'Content-Type': 'multipart/form-data',
        Authorization: `Bearer ${token}`,
      },
    };

    try {
      await axios.post(`${baseURL}/api/posts`, formData, config);
      setCategory('');
      setTags('');
      setTitle('');
      setText('');
      setImage(null);
      axios.get(`${baseURL}/api/posts`).then((response) => setPosts(response.data)); // Refresh posts
    } catch (error) {
      console.error('Error creating post:', error);
    }
  };

const handleCommentSubmit = async (event, postId) => {
    event.preventDefault();
    const token = localStorage.getItem("token");
    const userId = localStorage.getItem("user_id");
    const config = {
      headers:  {
        Authorization: `Bearer ${token}`,
      },
    };

  try {
    await axios.post(`${baseURL}/api/comments`, {
      text: commentText,
      post_id: postId,
      user_id: userId,
    }, config);
    setCommentText("");
    setCommentPostId(null)
    axios.get(`${baseURL}/api/posts`).then((response) => setPosts(response.data));
  } catch(error) {
    console.error("error adding comment: ", error);
  }
};

  return (
    <div className="main-page">
      <div className="top_half">
      <header>
        <h1>Welcome to Plant Shout</h1>
        <button onClick={handleLogout}>Logout</button>
      </header>
      <div className="info">
        <h2> To get Ai help select question in category.
          </h2>
        <h2> For no Ai help select discussion in category.
          </h2>
      </div>
      <div className="post-form">
        <h2>Create Post</h2>
        <form onSubmit={handleSubmit}>
          <select value={category} onChange={(e) => setCategory(e.target.value)} required>
            <option value="">Select Category</option>
            <option value="question">Question</option>
            <option value="discussion">Discussion</option>
          </select>
          <input
            type="text"
            placeholder="Tags"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            required
          />
          <input
            type="text"
            placeholder="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
          <textarea
            placeholder="Text Here"
            value={text}
            onChange={(e) => setText(e.target.value)}
            required
          ></textarea>
          {/*<input type="file" onChange={(e) => setImage(e.target.files[0])} /> */}
          {/* change this section when chatgpt api endpoint is fixed for images */}
          <button type="submit">Submit Post</button>
        </form>
        <h2> </h2>
      </div>
      </div>
      <div className="feed">
        {posts.map((post) => (
          <div key={post.id} className="post">
            <h2>{post.title}</h2>
            <h3>{post.text}</h3>
            <form onSubmit={(e) => handleCommentSubmit(e, post.id)}>
              <textarea
              placeholder = "Write a comment here"
              value = {commentPostId === post.id ? commentText : ""}
              onChange = {(e) => {
                setCommentPostId(post.id);
                setCommentText(e.target.value)
              }}
              required
              ></textarea>
              <button type="submit">Post Comment</button>
            </form>
            <div className="comments">
              {post.comments &&
                post.comments.map((comment) => (
                  <div key={comment.id} className="comment">
                    <div className="user_picture">
                    <img src={`${baseURL}/profile_pics/${comment.user_profile_pic}`} alt="Profile" />
                    </div>
                    <p>{comment.text}</p>
                  </div>
                ))}
              <div className="comment">
                <div clssName = "AI_picture">
                  <img src={AphidAI} alt="AphidAI" />
                </div>
                <p>{post.ai_response}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MainPage;


