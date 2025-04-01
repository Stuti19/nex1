import React from "react";
import ReactDOM from "react-dom/client"; // Required for React 18+
import App from "./App"; // Import the main App component
import "./index.css"; // Import global styles

// Find the root element in index.html
const rootElement = document.getElementById("root");
if (rootElement) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
} else {
  console.error("Root element not found. Make sure <div id='root'></div> is in index.html");
}