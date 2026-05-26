import React from 'react';

function Login() {
  return (
    <div>
      <h2>DealerKaki Login</h2>
      <form>
        <label>Username:</label>
        <input type="text" placeholder="Enter username" />
        <br />
        <label>Password:</label>
        <input type="password" placeholder="Enter password" />
        <br />
        <button type="submit">Login</button>
      </form>
    </div>
  );
}

export default Login;