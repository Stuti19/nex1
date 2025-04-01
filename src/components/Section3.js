import React from "react";
import "./Section3.css";

function Section3() {
  const changeTab = (tab) => {
    const images = {
      documents: "image/document.png",
      tables: "image/table.png",
      charts: "image/chart.png",
      slides: "image/slide.png",
    };
    document.getElementById("tabImage").src = images[tab];
  };

  return (
    <div className="section3">
      <h1>An AI-native workspace built for the future</h1>
      <div className="nav-tabs">
        <a className="active" onClick={() => changeTab("documents")}>
          Documents
        </a>
        <a onClick={() => changeTab("tables")}>Tables</a>
        <a onClick={() => changeTab("charts")}>Charts</a>
        <a onClick={() => changeTab("slides")}>Slides</a>
      </div>
      <div className="document-preview">
        <div className="document">
          <img id="tabImage" src="image/document.png" alt="Document Preview" />
        </div>
      </div>
    </div>
  );
}

export default Section3;