import React from "react";
import "./Section10.css";

function Section10() {
  return (
    <div className="section10-container">
      <p>Put Nex to work</p>
      <h1 className="section10-title">
        Hire your firm’s truly <br />
        Intelligent Copilot
      </h1>
      <a
        href="https://mail.google.com/mail/?view=cm&to=founder@compoundn.com"
        className="section10-contact-btn"
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
        Contact Us
      </a>
      <div className="section10-footer">
        <div className="section10-branding">
          <p className="section10-logo">
            <img src="image/logo.png" alt="Logo" /> Nex
          </p>
          <p className="section10-copyright">
            Raftel Private Limited 2025. All Rights Reserved
          </p>
        </div>
        <div className="section10-socials">
          <a href="">LinkedIn</a>
          <a href="">X</a>
        </div>
        <div className="section10-name">CompoundN</div>
      </div>
      <div className="bg-gradient"></div>
    </div>
  );
}

export default Section10;