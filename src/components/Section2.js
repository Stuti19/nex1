import React from "react";
import "./Section2.css";

function Section2() {
  return (
    <section className="section2">
      <div className="section2-column">
        <div className="section2-text section-text">
          Built to collaborate with you
        </div>
        <p>
          Answering questions and performing tasks like an analyst would, Nex
          reveals its thought process and grows with your team over time.
        </p>
      </div>
      <div className="center-line"></div>
      <div className="section2-column">
        <img src="image/section2.jpg" alt="Section 2" />
      </div>
    </section>
  );
}

export default Section2;