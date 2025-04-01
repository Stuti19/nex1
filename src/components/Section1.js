import React from "react";
import "./Section1.css";

function Section1() {
  return (
    <section className="section1">
      <div className="section1-heading">
        Meet Nex from CompoundN
        <br />
        <p>Your Copilot for Intelligent Investing</p>
      </div>
      <div className="section1-container">
        <div className="section1-column">
          <img src="image/section1photo.png" alt="Sample Image" />
          <div className="section1-1-text section-text">
            Delegate High Frequency Tasks
          </div>
          <p>
            Nex agents break down tasks into customizable plans with traceable
            steps. Automate your team's analytical legwork at scale.
          </p>
        </div>
        <div className="section1-column">
          <video autoPlay loop muted playsInline>
            <source src="image/section1vid.mp4" type="video/mp4" />
            Your browser does not support the video tag.
          </video>
          <div className="section1-1-text section-text">
            Reason over All of Your Data
          </div>
          <p>
            Nex unifies your internal files, external data, and trusted sources
            into a single searchable plane, enabling every analysis to be as
            comprehensive as possible.
          </p>
        </div>
      </div>
      <div className="section1-last">
        <img src="image/section1photo2.png" alt="Sample Image" />
        <video autoPlay loop muted playsInline>
          <source src="image/section1vid2.mp4" type="video/mp4" />
          Your browser does not support the video tag.
        </video>
      </div>
    </section>
  );
}

export default Section1;