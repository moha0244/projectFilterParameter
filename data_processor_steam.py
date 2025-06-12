import streamlit as st
import pandas as pd
from io import StringIO

def choice_column_filtered_parameter(df):
    with st.expander("Étape 1 : Sélectionner les colonnes à afficher", expanded=True):
        st.markdown("Choisissez les colonnes que vous souhaitez visualiser dans le tableau de données.")

        available_columns = df.columns.tolist()
        mode = st.selectbox("Mode de sélection des colonnes", ["Tout afficher", "Sélection personnalisée"], key="select_mode_param")

        if mode == "Tout afficher":
            selected_columns = available_columns
        else:
            selected_columns = st.multiselect(
                "Colonnes à inclure",
                options=available_columns,
                default=[],
                key="filter_columns_parameter"
            )

        if not selected_columns:
            st.warning("Veuillez sélectionner au moins une colonne.")
            return None

        return df[selected_columns]

def choice_column_filtered_search(selected_columns):
    with st.expander("Étape 2 : Sélectionner les colonnes à filtrer (facultatif)", expanded=True):
        st.markdown("Sélectionnez les colonnes sur lesquelles vous souhaitez appliquer des filtres dans la page suivante.")

        if not selected_columns:
            st.info("Aucune colonne n'a été sélectionnée à l'étape précédente.")
            return

        cols = st.columns(1)
        filter_columns = cols[0].multiselect(
            "Colonnes pour les filtres",
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
    st.title("Analyseur de données - Téléversement")
    uploaded_file = st.file_uploader("Téléversez un fichier CSV contenant la table", type=['csv'])

    if uploaded_file is not None:
        st.success("Fichier chargé avec succès. Passez à l'étape suivante pour sélectionner les données à afficher.")
        filtered_df = load_and_prepare_data(uploaded_file)
        if filtered_df is not None:
            choice_column_filtered_search(filtered_df.columns.tolist())
            st.session_state.original_df = filtered_df
            st.session_state.current_df = filtered_df.copy()
            if st.button("Afficher les données"):
                st.session_state.page = "data_viewer"
                st.rerun()
        else:
            st.error("Impossible de traiter le fichier par manque d'informations.")

def data_viewer_page():
    st.title("Analyseur de données - Visualisation")

    if 'original_df' not in st.session_state:
        st.warning("Aucun fichier chargé. Veuillez d'abord téléverser un fichier.")
        if st.button("Retour à l'étape précédente"):
            st.session_state.page = "main"
            st.rerun()
        return

    if 'filter_reset_counter' not in st.session_state:
        st.session_state.filter_reset_counter = False

    with st.sidebar:
        st.header("Filtres dynamiques")

        filter_columns = st.session_state.get("filter_columns", [])
        df = st.session_state.original_df.copy()

        for col in filter_columns:
            if col not in df.columns:
                continue

            unique_values = get_unique_column_values(st.session_state.original_df, col)
            selectbox_key = f"filter_{col}_{st.session_state.filter_reset_counter}"

            if df[col].dtype == object:
                val = st.selectbox(f"{col}", [''] + unique_values, key=selectbox_key)
                if val:
                    df = df[df[col] == val]
            else:
                unique_vals = sorted(df[col].dropna().unique())
                int_options = [int(v) for v in unique_vals]
                val = st.selectbox(f"{col}", [''] + [str(i) for i in int_options], key=selectbox_key)
                if val:
                    df = df[df[col] == int(val)]

        st.session_state.current_df = df

        if len(st.session_state.filter_columns) == 0:
            st.info("Aucun filtre sélectionné.")

        elif st.button("Réinitialiser les filtres"):
            st.session_state.current_df = st.session_state.original_df.copy()
            st.session_state.filter_reset_counter = True
            st.rerun()

        if st.button("Retour au téléversement"):
            st.session_state.page = "main"
            st.rerun()

    st.subheader("Données filtrées")
    st.dataframe(st.session_state.current_df)

    csv = st.session_state.current_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Télécharger les données filtrées au format CSV",
        data=csv,
        file_name='donnees_filtrees.csv',
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
