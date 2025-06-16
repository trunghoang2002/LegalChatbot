import React, { useState } from "react";
import emailIcon from "../img/email.svg";
import passwordIcon from "../img/password.svg";
import styles from "./SignUp.module.css";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { notify } from "./toast";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { API_URLS } from '../config';

const SignIn = () => {
  const [data, setData] = useState({
    email: "",
    password: "",
  });

  const [touched, setTouched] = useState({});
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const changeHandler = (event) => {
    if (event.target.name === "IsAccepted") {
      setData({ ...data, [event.target.name]: event.target.checked });
    } else {
      setData({ ...data, [event.target.name]: event.target.value });
    }
  };

  const focusHandler = (event) => {
    setTouched({ ...touched, [event.target.name]: true });
  };

  const submitHandler = (event) => {
    event.preventDefault();
    setLoading(true);
    // const urlApi = 'http://localhost:5000/login';
    const checkData = async () => {
      try {
        // const response = await axios.post(urlApi, {
        const response = await axios.post(API_URLS.LOGIN, {
          email: data.email.toLowerCase(),
          password: data.password,
        });
        if (response.status === 200) {
          notify("Signed in successfully", "success");
          localStorage.setItem('token', response.data.access_token);
          navigate('/chat');
        } else {
          notify("Your password or your email is wrong", "error");
        }
      } catch (error) {
        if (error.response && error.response.status === 401) {
          notify("Wrong email or password", "error");
        } else {
          notify("Something went wrong", "error");
        }
      } finally {
        setLoading(false);
      }
    };
    checkData();
  };

  return (
    <div className={styles.container}>
      <form className={styles.formLogin} onSubmit={submitHandler} autoComplete="off">
        <h2>Sign In</h2>
        <div>
          <div>
            <input type="text" name="email" value={data.email} placeholder="E-mail" onChange={changeHandler} onFocus={focusHandler} autoComplete="off" />
            <img src={emailIcon} alt="" />
          </div>
        </div>
        <div>
          <div>
            <input type="password" name="password" value={data.password} placeholder="Password" onChange={changeHandler} onFocus={focusHandler} autoComplete="off" />
            <img src={passwordIcon} alt="" />
          </div>
        </div>
        <div>
          <button type="submit" disabled={loading}>
            {loading ? "Loading..." : "Login"}
          </button>
          <span style={{ color: "#ffffff", textAlign: "center", display: "inline-block", width: "100%" }}>
            Don't have an account? <Link className={styles.link} to="/signup">Create account</Link>
          </span>
        </div>
      </form>
      <ToastContainer />
    </div>
  );
};

export default SignIn;