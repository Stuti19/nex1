import React from "react";
import "./Section7.css";

function Section7() {
  return (
    <section className="section7">
      <div className="section7-column">
        <div className="section7-text section-text">
          Enterprise-Grade Security
        </div>
        <p>
          All customer data is encrypted both in transit and at rest, utilizing
          the most robust encryption standards: AES-256 for storage and TLS
          1.2/1.3 for secure communication.
        </p>
      </div>
      <div className="center-line"></div>
      <div className="section7-column">
        <img src="image/section7.png" alt="Section 7" />
      </div>
    </section>
  );
}

export default Section7;