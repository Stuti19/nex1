import React, { useState, useEffect } from "react";
import "./Login.css";
import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider, signInWithPopup } from "firebase/auth";
import emailjs from "@emailjs/browser";
import { useNavigate } from "react-router-dom"; // Import useNavigate

function Login() {
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [serverOtp, setServerOtp] = useState("");
  const [userEmail, setUserEmail] = useState("");
  const [message, setMessage] = useState("");
  const [isOtpSent, setIsOtpSent] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const navigate = useNavigate(); // Initialize useNavigate

  // Firebase configuration
  const firebaseConfig = {
    apiKey: "AIzaSyDbV-ZWkdlxCe0ZF292MtktP6ang02O_44",
    authDomain: "compoundn-9ab19.firebaseapp.com",
    projectId: "compoundn-9ab19",
    storageBucket: "compoundn-9ab19.firebasestorage.app",
    messagingSenderId: "693090646341",
    appId: "1:693090646341:web:f2c40951e4a84eb26ea62c",
  };

  // Initialize Firebase
  useEffect(() => {
    const app = initializeApp(firebaseConfig);
    const auth = getAuth(app);
    const provider = new GoogleAuthProvider();
    emailjs.init("7nQu3UN4-ahIsdOMm");
  }, []);

  const generateOTP = () => {
    return Math.floor(100000 + Math.random() * 900000).toString();
  };

  const sendOTPEmail = async (email, otp) => {
    try {
      const templateParams = {
        to_email: email,
        otp: otp,
        from_name: "CompoundN",
      };

      await emailjs.send(
        "service_td5dqww",
        "template_brvz16j",
        templateParams
      );

      return true;
    } catch (error) {
      console.error("Error sending email:", error);
      return false;
    }
  };

  const handleSendOtp = async (e) => {
    e.preventDefault();
    setMessage("");
    setIsLoading(true);

    if (!email) {
      setMessage("Please enter your email.");
      setIsLoading(false);
      return;
    }

    const otp = generateOTP();
    const emailSent = await sendOTPEmail(email, otp);

    if (emailSent) {
      setServerOtp(otp);
      setUserEmail(email);
      setIsOtpSent(true);
      setMessage(`OTP sent to ${email}. Please check your inbox.`);
    } else {
      setMessage("Failed to send OTP. Please try again.");
    }

    setIsLoading(false);
  };

  const handleVerifyOtp = (e) => {
    e.preventDefault();
    setMessage("");

    if (otp === serverOtp) {
      setMessage("OTP verified successfully! Redirecting...");
      setTimeout(() => {
        navigate("/reportviewer"); // Redirect to ReportViewer page
      }, 1500);
    } else {
      setMessage("Invalid OTP. Please try again.");
    }
  };

  const handleGoogleLogin = async () => {
    setMessage("");
    setIsLoading(true);

    try {
      const provider = new GoogleAuthProvider();
      provider.setCustomParameters({
        prompt: "select_account",
      });

      const result = await signInWithPopup(getAuth(), provider);
      if (result.user) {
        setMessage("Google login successful! Redirecting...");
        setTimeout(() => {
          navigate("/reportviewer"); // Redirect to ReportViewer page
        }, 1500);
      }
    } catch (error) {
      console.error("Google login error:", error);
      setMessage(error.message || "Failed to login with Google. Please try again.");
    }

    setIsLoading(false);
  };

  return (
    <div className="login-page">
    <div className="login-container">
      <h3>Welcome to CompoundN</h3>
      {message && <div className={`message ${isOtpSent ? "success" : "error"}`}>{message}</div>}

      {!isOtpSent ? (
        <form onSubmit={handleSendOtp}>
          <button
            type="button"
            className="google-btn"
            onClick={handleGoogleLogin}
            disabled={isLoading}
          >
            <img src="https://www.google.com/favicon.ico" alt="Google" />
            Continue with Google
          </button>

          <div className="divider">
            <span>OR</span>
          </div>

          <div>
            <label>Email:</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="Enter your email"
            />
          </div>
          <button type="submit" disabled={isLoading}>
            {isLoading ? "Sending..." : "Send OTP"}
          </button>
        </form>
      ) : (
        <form onSubmit={handleVerifyOtp}>
          <div>
            <label>Enter OTP sent to {userEmail}:</label>
            <input
              type="text"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              required
              placeholder="Enter OTP"
              maxLength="6"
            />
          </div>
          <button type="submit">Verify OTP</button>
          <button
            type="button"
            className="resend-button"
            onClick={() => setIsOtpSent(false)}
          >
            Back to Email
          </button>
        </form>
      )}
    </div>
    </div>
  );
}

export default Login;