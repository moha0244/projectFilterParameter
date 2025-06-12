import streamlit as st
import pandas as pd
from io import StringIO


def choice_column_filtered_parameter(df):
    with st.expander(" Sélection les paramètres que vous voulez afficher", expanded=True):
        st.markdown("### Sélection des colonnes à afficher")

        available_columns = df.columns.tolist()
        mode = st.selectbox("Mode de sélection :", ["Tout", "Personnalisé"], key="select_mode_param")

        if mode == "Tout":
            selected_columns = available_columns
        else:
            selected_columns = st.multiselect(
                "Colonnes à inclure dans l’analyse",
                options=available_columns,
                default=[],
                key="filter_columns_parameter"
            )

        if not selected_columns:
            st.warning("Veuillez sélectionner au moins une colonne.")
            return None

        return df[selected_columns]



def choice_column_filtered_Search(selected_columns):
    with st.expander(" Sélection des colonnes à filtrer (facultatif)", expanded=True):
        st.markdown("Choisissez les colonnes pour les filtres dynamiques dans la page suivante :")

        if not selected_columns:
            st.info("Aucune colonne sélectionnée précédemment.")
            return

        cols = st.columns(1)

        filter_columns = cols[0].multiselect(
            "choix de filtre de recherche",
            options=selected_columns,
            default=[],
            key="filter"
        )

        st.session_state.filter_columns = filter_columns



def read_csv_file(uploaded_file):
    if uploaded_file is None:
        return None

    for delimiter in [',', ';']:
        for encoding in ['utf-8', 'latin1']:
            try:
                content = uploaded_file.getvalue().decode(encoding)
                df = pd.read_csv(StringIO(content), delimiter=delimiter, low_memory=False)
                if df.shape[1] > 1:
                    return df
            except Exception:
                continue
    return None


def load_and_prepare_data(uploaded_file):
    df = read_csv_file(uploaded_file)
    if df is None:
        return df



    return choice_column_filtered_parameter(df)


def get_unique_column_values(df, column_name):
    try:
        if column_name in df.columns:
            unique_values = df[column_name].unique().tolist()
            return [str(val) for val in unique_values if pd.notna(val)]
        return []
    except Exception:
        return []


def main_page():
    st.title("Data Processor - Upload")
    uploaded_file = st.file_uploader("Upload CSV file", type=['csv'])

    if uploaded_file is not None:
        st.success("File loaded successfully! Click the button below to view the data.")
        filtered_df = load_and_prepare_data(uploaded_file)
        if filtered_df is not None:
            choice_column_filtered_Search(filtered_df.columns.tolist())
            st.session_state.original_df = filtered_df
            st.session_state.current_df = filtered_df.copy()
            st.session_state.file_uploaded = True
            if st.button("View Data"):
                st.session_state.page = "data_viewer"
                st.rerun()
        else:
            st.error("Could not process the file. Please check the format.")


def data_viewer_page():
    st.title("Data Processor - Viewer")

    if 'original_df' not in st.session_state:
        st.warning("No data available. Please upload a file first.")
        if st.button("Back to Upload"):
            st.session_state.page = "main"
            st.rerun()
        return

    # Initialisation du compteur de reset
    if 'filter_reset_counter' not in st.session_state:
        st.session_state.filter_reset_counter = False


    with st.sidebar:
        st.header("Filtrer selon les colonnes que vous avez choisi ")

        filter_columns = st.session_state.get("filter_columns", [])
        df = st.session_state.original_df.copy()

        for col in filter_columns:
            if col not in df.columns:
                continue

            unique_values = get_unique_column_values(st.session_state.original_df, col)


            selectbox_key = f"filter_{col}_{st.session_state.filter_reset_counter}"

            if df[col].dtype == object:
                val = st.selectbox(f"{col} :", [''] + unique_values,
                                   key=selectbox_key)
                if val:
                    df = df[df[col] == val]
            else:
                unique_vals = sorted(df[col].dropna().unique())
                int_options = [int(v) for v in unique_vals]
                val = st.selectbox(f"{col} :", [''] + [str(i) for i in int_options],
                                   key=selectbox_key)
                if val:
                    df = df[df[col] == int(val)]

        st.session_state.current_df = df

        if len(st.session_state.filter_columns) == 0:
            st.warning("Aucun filtre n'a été sélectionné.")

        elif st.button("Reset Filters") :
            st.session_state.current_df = st.session_state.original_df.copy()
            st.session_state.filter_reset_counter =True
            st.rerun()


        if st.button("Back to Upload"):
            st.session_state.page = "main"
            st.rerun()

    # Main content area
    st.dataframe(st.session_state.current_df)

    # Download button
    csv = st.session_state.current_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name='filtered_data.csv',
        mime='text/csv',
    )


def main():
    if 'page' not in st.session_state:
        st.session_state.page = "main"

    if st.session_state.page == "main":
        main_page()
    elif st.session_state.page == "data_viewer":
        data_viewer_page()


if __name__ == "__main__":
    main()