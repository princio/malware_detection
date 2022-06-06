<template>
  <div id="app">
    <div id="nav">
      <router-link to="/">Home</router-link> |
      <router-link to="/applies">Applies</router-link> |
      <router-link to="/pcaps">Pcaps</router-link> |
      <router-link to="/about">About</router-link>
    </div>
    <router-view/>
  </div>
</template>

<style>
body {
  margin: 0;
  background-color: rgb(53, 53, 53);
}

#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: white; /*#2c3e50;*/
}

#nav {
  padding: 30px;
}

#nav a {
  font-weight: bold;
  color: lightcyan; /*#2c3e50;*/
}

#nav a.router-link-exact-active {
  color: lightgreen; /* #42b983 */
}

.checkbox-button {
    margin:2px;
    background-color:#EFEFEF;
    border-radius:4px;
    border:1px solid #D0D0D0;
    overflow:auto;
    float:left;
    color: black
}

.checkbox-button {
    margin:2px;
    background-color:#EFEFEF;
    border-radius:4px;
    border:1px solid #D0D0D0;
    overflow:auto;
    float:left;
}

.checkbox-button:hover {
    /* margin:2px; */
    background-color:#EFEFEF;
    border-radius:4px;
    border:1px solid red;
    overflow:auto;
    float:left;
    color:red;
}

.checkbox-button  label {
    float:left;
    width:2.0em;
}

.checkbox-button label span {
    text-align:center;
    padding:3px 0px;
    display:block;
}

.checkbox-button label input {
    position:absolute;
    top:-20px;
}

.checkbox-button input:checked + span {
    background-color:#911;
    color:#fff;
}
</style>
