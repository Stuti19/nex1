import React from "react";
import "./Section4.css";

function Section4() {
  return (
    <div className="section4">
      {/* Left Column */}
      <div className="section4-column">
        <video autoPlay loop muted playsInline>
          <source src="image/section4.mp4" type="video/mp4" />
          Your browser does not support the video tag.
        </video>
        <div className="section4-1-text section-text">
          LLMs Engineered for Finance
        </div>
        <p>
          Custom-built models designed to understand the intricacies of
          financial concepts and documents: P&Ls, accounting methodologies,
          diligence files, and more.
        </p>
      </div>

      {/* Right Column */}
      <div className="section4-column">
        <video autoPlay loop muted playsInline>
          <source src="image/section4-2.mp4" type="video/mp4" />
          Your browser does not support the video tag.
        </video>
        <div className="section4-1-text section-text">
          Traceable from Start to Finish
        </div>
        <p>
          Nex provides integrated citations, augmenting outputs with attribution
          to underlying sources.
        </p>
      </div>
    </div>
  );
}

export default Section4;