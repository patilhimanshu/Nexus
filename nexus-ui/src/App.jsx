import { useState } from "react";

export default function App() {

  const [messages, setMessages] = useState([
    {
      sender: "Nexus",
      text: "Hello Himanshu! 👋"
    }
  ]);

  const [input, setInput] = useState("");

  function sendMessage() {

    if (input.trim() === "") return;

    const userMessage = {
      sender: "You",
      text: input
    };

    setMessages(prev => [...prev, userMessage]);

    const currentInput = input;

    setInput("");

    // Fake AI Response
    setTimeout(() => {

      const aiMessage = {
        sender: "Nexus",
        text: "You said: " + currentInput
      };

      setMessages(prev => [...prev, aiMessage]);

    },1000);

  }

  return (

    <div style={styles.page}>

      <div style={styles.sidebar}>

        <h2>🤖 Nexus</h2>

        <button>+ New Chat</button>

      </div>

      <div style={styles.chatContainer}>

        <div style={styles.messages}>

          {messages.map((msg,index)=>(

            <div
              key={index}
              style={{
                ...styles.message,
                background:
                  msg.sender==="You"
                  ? "#3B82F6"
                  : "#2D3748"
              }}
            >

              <strong>{msg.sender}</strong>

              <br/>

              {msg.text}

            </div>

          ))}

        </div>

        <div style={styles.inputArea}>

          <input

            value={input}

            onChange={(e)=>setInput(e.target.value)}

            placeholder="Ask Nexus..."

            style={styles.input}

          />

          <button
            onClick={sendMessage}
          >

            Send

          </button>

        </div>

      </div>

    </div>

  );

}

const styles={

page:{
display:"flex",
height:"100vh",
background:"#111827",
color:"white",
fontFamily:"Arial"
},

sidebar:{
width:"250px",
background:"#1F2937",
padding:"20px"
},

chatContainer:{
flex:1,
display:"flex",
flexDirection:"column"
},

messages:{
flex:1,
overflowY:"auto",
padding:"20px"
},

message:{
padding:"12px",
marginBottom:"10px",
borderRadius:"10px",
maxWidth:"60%"
},

inputArea:{
display:"flex",
padding:"20px",
gap:"10px"
},

input:{
flex:1,
padding:"12px",
borderRadius:"8px",
border:"none"
}

}