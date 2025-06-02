import os

import streamlit as st
from config import INPUT_DIRECTORY
from tools.tool import Tool

from maps4fs.toolbox.custom_osm import fix_osm_file


class FixCustomOsmFile(Tool):
    title = "Fix a custom OSM file"
    description = (
        "This tool tries to fix a custom OSM file by removing all incorrect entries. "
        "It does not guarantee that the file will be fixed, if some specific errors are "
        "present in the file, since the tool works with a common set of errors."
    )
    icon = "🛠️"

    save_path = None
    download_path = None

    def content(self):
        st.warning(
            "DEPRECATION WARNING: This tool is deprecated and will be removed in maps4fs 2.0. "
            "It will be integrated into the maps4fs generator and will not be available as "
            "a separate tool. "
            "If you want to continue using this tool, do not update maps4fs to 2.0."
        )
        if "fixed_osm" not in st.session_state:
            st.session_state.fixed_osm = False
        uploaded_file = st.file_uploader(
            "Upload a custom OSM file", type=["osm"], key="osm_uploader"
        )

        if uploaded_file is not None:
            self.save_path = self.get_save_path(uploaded_file.name)
            with open(self.save_path, "wb") as f:
                f.write(uploaded_file.read())

            base_name = os.path.basename(self.save_path).split(".")[0]
            output_name = f"{base_name}_fixed.osm"
            self.download_path = self.get_save_path(output_name)

            if st.button("Fix the file", icon="▶️"):
                try:
                    result, number_of_errors = fix_osm_file(self.save_path, self.download_path)
                except Exception as e:
                    st.error(
                        f"The file is completely broken it's even impossible to read it. Error: {e}"
                    )
                    return

                st.success(f"Fixed the file with {number_of_errors} errors.")
                if result:
                    st.success("The file was read successfully.")
                else:
                    st.error("Even after fixing, the file could not be read.")

                st.session_state.fixed_osm = True

        if st.session_state.fixed_osm:
            with open(self.download_path, "rb") as f:
                st.download_button(
                    label="Download",
                    data=f,
                    file_name=f"{self.download_path.split('/')[-1]}",
                    mime="application/zip",
                    icon="📥",
                )

            st.session_state.fixed_osm = False

    def get_save_path(self, file_name: str) -> str:
        """Get the path to save the file in the input directory.

        Arguments:
            file_name {str} -- The name of the  file.

        Returns:
            str -- The path to save the file in the input directory.
        """
        return os.path.join(INPUT_DIRECTORY, file_name)
