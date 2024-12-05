import streamlit as st


class Tool:
    title: str
    description: str
    icon: str | None

    def __init__(self):
        with st.expander(self.title, icon=self.icon):
            st.write(self.description)
            self.content()

    def content(self):
        raise NotImplementedError
