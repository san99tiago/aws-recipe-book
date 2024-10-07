import "../styles/Dashboard.css";
import { Header } from "./Header";
import { useEffect, useState } from "react";
import userpool from "./userpool";
import { useNavigate } from "react-router-dom";
import * as jose from "jose";
import { v4 as uuidv4 } from "uuid";
import GLOBAL_VARS from "../GLOBAL_VARS";

function Dashboard() {
  // Set global vars
  const VITE_BACKEND_API_URL = GLOBAL_VARS.VITE_BACKEND_API_URL;

  const navigate = useNavigate();
  const [userEmail, setUserEmail] = useState("");
  const [recipeItems, setRecipeItems] = useState([]);
  const [newTitle, setNewTitle] = useState("");

  useEffect(() => {
    let user = userpool.getCurrentUser();
    console.log(`user is: ${JSON.stringify(user)}`);

    if (!user) {
      navigate(`/home`);
    }
    try {
      // Get user details to populate page
      const clientId = user?.pool?.clientId;
      const username = user?.username;
      console.debug(`username is: ${username}, clientId is: ${clientId}`);

      const idTokenKey = `CognitoIdentityServiceProvider.${clientId}.${username}.idToken`;
      const idToken = user?.storage[idTokenKey];
      const decodedToken = jose.decodeJwt(idToken);
      let userName = user?.username;
      let userEmailText = decodedToken.email;
      let userFullName = decodedToken.name;
      console.debug(`decodedToken is: ${JSON.stringify(decodedToken)}`);
      console.log(
        `userName is: ${userName}, userEmail is: ${userEmailText}, userFullName is: ${userFullName}`
      );
      setUserEmail(userEmailText);

      // Fetch RECIPE items
      const myHeaders = new Headers();
      let correlationId = `santi-${uuidv4()}`;
      myHeaders.append("Correlation-ID", correlationId);
      myHeaders.append("Authorization", idToken);

      const requestOptions = {
        method: "GET",
        headers: myHeaders,
        redirect: "follow",
      };

      let getRecipesPath =
        VITE_BACKEND_API_URL + `/recipes?user_email=${userEmailText}`;
      console.log(`getRecipesPath is: ${getRecipesPath}`);

      // Fetch the RECIPE items
      fetch(getRecipesPath, requestOptions)
        .then((response) => response.json())
        .then((data) => {
          console.log(`fetched_data: ${data}`);
          setRecipeItems(data);
        })
        .catch((error) => {
          console.error("Error:", error);
        });
    } catch (error) {
      setUserEmail("");
    }
  }, []);

  // **************************
  // Create a new RECIPE item
  // **************************

  const deleteItem = async (sk) => {
    console.log(`Starting deleteItem with sk: ${sk}`);
    let recipeId = sk.replace("RECIPE#", "");
    let deleteRecipePath =
      VITE_BACKEND_API_URL + `/recipes/${recipeId}?user_email=${userEmail}`;
    console.log(`deleteRecipePath is: ${deleteRecipePath}`);

    let user = userpool.getCurrentUser();
    console.log(`user is: ${JSON.stringify(user)}`);

    if (!user) {
      navigate(`/home`);
    }

    // Get user details to populate page
    const clientId = user?.pool?.clientId;
    const username = user?.username;
    console.debug(`username is: ${username}, clientId is: ${clientId}`);

    const idTokenKey = `CognitoIdentityServiceProvider.${clientId}.${username}.idToken`;
    const idToken = user?.storage[idTokenKey];
    const decodedToken = jose.decodeJwt(idToken);
    let userName = user?.username;
    let userEmailText = decodedToken.email;
    let userFullName = decodedToken.name;
    console.debug(`decodedToken is: ${JSON.stringify(decodedToken)}`);
    console.log(
      `userName is: ${userName}, userEmail is: ${userEmailText}, userFullName is: ${userFullName}`
    );
    setUserEmail(userEmailText);

    try {
      // Fetch RECIPE items
      const myHeaders = new Headers();
      let correlationId = `santi-${uuidv4()}`;
      myHeaders.append("Correlation-ID", correlationId);
      myHeaders.append("Authorization", idToken);

      const response = await fetch(deleteRecipePath, {
        method: "DELETE",
        headers: myHeaders,
        redirect: "follow",
      });

      if (!response.ok) {
        throw new Error("Error deleting item");
      }

      // Remove the deleted item from the state
      setRecipeItems(recipeItems.filter((item) => item.SK !== sk));
    } catch (error) {
      console.error("Failed to delete item:", error);
    }
  };

  // **************************
  // Create a new RECIPE item
  // **************************
  const createItem = async (event) => {
    event.preventDefault();
    console.log(`Starting createItem with newTitle: ${newTitle}`);

    let user = userpool.getCurrentUser();
    console.log(`user is: ${JSON.stringify(user)}`);

    if (!user) {
      navigate(`/home`);
    }

    // Get user details to populate page
    const clientId = user?.pool?.clientId;
    const username = user?.username;
    console.debug(`username is: ${username}, clientId is: ${clientId}`);

    const idTokenKey = `CognitoIdentityServiceProvider.${clientId}.${username}.idToken`;
    const idToken = user?.storage[idTokenKey];
    const decodedToken = jose.decodeJwt(idToken);
    let userName = user?.username;
    let userEmailText = decodedToken.email;
    let userFullName = decodedToken.name;
    console.debug(`decodedToken is: ${JSON.stringify(decodedToken)}`);
    console.log(
      `userName is: ${userName}, userEmail is: ${userEmailText}, userFullName is: ${userFullName}`
    );
    setUserEmail(userEmailText);

    try {
      // Create RECIPE items
      let createRecipePath = VITE_BACKEND_API_URL + `/recipes`;
      console.log(`createRecipePath is: ${createRecipePath}`);

      const myHeaders = new Headers();
      let correlationId = `santi-${uuidv4()}`;
      myHeaders.append("Correlation-ID", correlationId);
      myHeaders.append("Authorization", idToken);
      myHeaders.append("Content-Type", "application/json");

      const response = await fetch(createRecipePath, {
        method: "POST",
        headers: myHeaders,
        redirect: "follow",
        body: JSON.stringify({
          user_email: userEmailText,
          recipe_title: newTitle,
          recipe_details: "Default details",
          recipe_date: "2025-12-31",
        }),
      });

      if (!response.ok) {
        throw new Error("Error creating item");
      }
      const newItem = await response.json();
      setRecipeItems([...recipeItems, newItem]);
      // Remove existing text from the input field
      // Clear the input field
      document.getElementById("newItem").value = "";
    } catch (error) {
      console.error("Failed to create item:", error);
    }
  };

  return (
    <>
      <Header userEmail={userEmail} />
      <div className="container-fluid p-3">
        <h1 className="text-align-top">Recipes App</h1>

        <form id="form-create-recipes" onSubmit={createItem}>
          <div className="form-group">
            <div className="form-row">
              <label htmlFor="newItem" className="h3">
                New Item:
              </label>
              <input
                type="text"
                id="newItem"
                className="form-control"
                aria-describedby="newItemHelp"
                placeholder="Enter Item Title"
                onChange={(e) => setNewTitle(e.target.value)}
              />
              <small id="newItemHelp" className="form-text text-muted">
                Add items to your RECIPE list!
              </small>
            </div>
          </div>
          <button type="submit" className="btn btn-primary">
            Submit
          </button>
        </form>

        <div className="container main-box">
          <h3>Recipe Items:</h3>
          <div className="list-group">
            <div className="container-fluid p-12" id="main-box">
              {recipeItems.map((item) => (
                <div key={item.SK} className="row">
                  <div className="col list-group-item d-flex align-items-center justify-content-between">
                    <label className="p mb-0">
                      <input type="checkbox" className="mr-2" />
                    </label>
                    <h3>{item.recipe_title}</h3>
                    <p>{item.recipe_details}</p>
                    <button
                      className="btn btn-danger"
                      onClick={() => deleteItem(item.SK)}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default Dashboard;
