import React from "react";
import { Link } from "react-router-dom"; // Import Link from react-router-dom
import "./Navbar.css";

function Navbar() {
  const toggleMenu = () => {
    document.getElementById("fullscreenMenu").classList.toggle("show");
  };

  return (
    <nav className="navbar">
      <div className="logo">
        <img src="image/logo.png" alt="Logo" />
        <span style={{ marginLeft: "8px", fontWeight: 500 }}>CompoundN</span>
      </div>
      <div className="auth-buttons">
        {/* Replace <a href="login.html"> with <Link to="/login"> */}
        <Link to="/login" className="login-btn" id="loginBtn">
          Log in
        </Link>
        <a
          href="https://mail.google.com/mail/?view=cm&to=founder@compoundn.com"
          className="contact-btn"
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
      <div className="menu-icon" onClick={toggleMenu}>
        ☰
      </div>
      <div className="fullscreen-menu" id="fullscreenMenu">
        <span className="close-menu" onClick={toggleMenu}>
          ✖
        </span>
        <a href="login.html" className="login-btn">
          Log in
        </a>
        <a
          href="https://mail.google.com/mail/?view=cm&to=founder@compoundn.com"
          className="contact-btn"
        >
          Contact Founder
        </a>
      </div>
    </nav>
  );
}

export default Navbar;