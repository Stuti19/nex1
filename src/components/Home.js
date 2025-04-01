import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Home.css';

const Home = () => {
  const navigate = useNavigate();

  return (
    <div className="home-container">
      <div className="hero-section">
        <h1>CompoundN</h1>
        <h2 className="subtitle">Co-pilot for investing</h2>
        <p className="description">Get detailed financial reports</p>
        <button className="cta-button" onClick={() => navigate('/login')}>
          Get Started →
        </button>
      </div>
      
      <div className="features-section">
        <div className="feature-card">
          <h3>Fast</h3>
          <p>Real-time streamed responses</p>
        </div>
        <div className="feature-card">
          <h3>Modern</h3>
          <p>Get the latest reports</p>
        </div>
        <div className="feature-card">
          <h3>Smart</h3>
          <p>Meet your AI Companion that goes beyond the conversation</p>
        </div>
      </div>
    </div>
  );
};

export default Home; 