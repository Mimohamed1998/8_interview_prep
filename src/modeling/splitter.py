def time_split(df, train_end, eval_start):
    """Split DataFrame into train and eval sets on year_month.

    Returns:
        Tuple of (df_train, df_eval).
    """
    df_train = df[df["year_month"] <= train_end].copy()
    df_eval = df[df["year_month"] >= eval_start].copy()
    return df_train, df_eval
