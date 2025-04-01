import React from "react";
import { Link } from "react-router-dom"; // Import Link from react-router-dom
import "./HeroSection.css";

function HeroSection() {
  return (
    <section className="hero">
      <div className="hero-content">
        <h1 className="hero-title">
          AI Copilot for <br /> Intelligent Investing
        </h1>
        <div className="hero-buttons">
          {/* Replace href with Link to ReportViewer */}
          <Link to="/login" className="primary-btn">
            Get Started
          </Link>
          <a
            href="https://mail.google.com/mail/?view=cm&to=founder@compoundn.com"
            className="secondary-btn"
          >
            <svg
              className="arrow-icon"
              viewBox="0 0 16 16"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M3 8H13M13 8L9 4M13 8L9 12"
                stroke="white"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            Contact Founder
          </a>
        </div>
      </div>
      <div className="feature-box">
        <div className="feature-header">
          <div className="logo">
            <img src="image/logo.png" alt="Logo" />
          </div>
          <span className="feature-title">Introducing Nex</span>
        </div>
        <p className="feature-description">
          World’s best copilot for Intelligent Investing. Optimize your team's
          most common workflows and enhance the quality of every output.
        </p>
      </div>
      <div className="bg-gradient"></div>
    </section>
  );
}

export default HeroSection;