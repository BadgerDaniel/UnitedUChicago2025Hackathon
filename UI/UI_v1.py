import streamlit as st

st.set_page_config(layout="wide")

# Create two columns with a 1:2 ratio (left:right)
left_col, right_col = st.columns([1, 2])

# Left Column: Split vertically using containers
with left_col:
    with st.container():
        st.subheader("Top 5 Trending Events")
        # Placeholder content
        for i in range(1, 6):
            st.markdown(f"**Event {i}**: Description goes here.")

    st.divider()  # Visual separator

    with st.container():
        st.subheader("Top Price Movers")
        # Placeholder content
        for i in range(1, 6):
            st.markdown(f"**Asset {i}**: +X%")

# Right Column: Chat window placeholder
with right_col:
    st.subheader("Chat Window")
    st.chat_message("assistant").write("Hi! Ask me anything about the trends or prices.")
    if prompt := st.chat_input("Ask your question..."):
        st.chat_message("user").write(prompt)
        # Replace below with your LLM response call
        st.chat_message("assistant").write(f"You said: {prompt}")
