from beeflow.common.cwl.workflow import Task, Input, Output, Workflow, Charliecloud

def main():
    """Create the fire workflow."""
    # Define common inputs
    csv_path = Input("csv_path", "string", "./data/data.csv", prefix="--csv_path")
    encoder_path = Input("encoder_path", "string", "./models/encoder.joblib", prefix="--encoder_path")
    area_features = Input("area_features", "string", "wind_speed wdir smois fuels ignition", prefix="--features")
    test_size = Input("test_size", "float", 0.2, prefix="--test_size")
    random_seed = Input("random_seed", "int", 42, prefix="--random_seed")
    area_data_dir = Input("area_data_dir", "string", "./data/area", prefix="--data_path")
    data_scaler = Input("data_scaler", "string", "StandardScaler", prefix="--data_scaler")
    behaviour_features = Input("behaviour_features", "string", "wind_speed wdir smois fuels ignition", prefix="--features")
    behaviour_target = Input("behaviour_target", "string", "safe_unsafe_fire_behavior", prefix="--target")
    behaviour_data_dir = Input("behaviour_data_dir", "string", "./data/behaviour", prefix="--data_path")
    area_models_dir = Input("area_models_dir", "string", "./models/area", prefix="--model_dir_path")
    area_metrics_dir = Input("area_metrics_dir", "string", "./metrics/area", prefix="--metric_output_dir")
    common_gridsearch_kwargs = Input("common_gridsearch_kwargs", "string", "'{\"n_jobs\":-1,\"verbose\":3}'", prefix="--gridsearch_kwargs")
    rf_area_name = Input("rf_area_name", "string", "random_forest_regressor", prefix="--name")
    behaviour_models_dir = Input("behaviour_models_dir", "string", "./models/behaviour", prefix="--model_dir_path")
    behaviour_metrics_dir = Input("behaviour_metrics_dir", "string", "./metrics/behaviour", prefix="--metric_output_dir")
    rf_behaviour_name = Input("rf_behaviour_name", "string", "random_forest_classifier", prefix="--name")
    area_metrics = Input("area_metrics", "string", "'[{\"name\":\"mean_absolute_error\",\"params\":{}},{\"name\":\"mean_squared_error\",\"params\":{}},{\"name\":\"r2_score\",\"params\":{}}]'", prefix="--metrics_info")
    area_predictions_dir = Input("area_predictions_dir", "string", "./data/area", prefix="--npy_output_dir")
    behaviour_metrics = Input("behaviour_metrics", "string", "'[{\"name\":\"precision_score\",\"params\":{\"average\":\"weighted\"}},{\"name\":\"recall_score\",\"params\":{\"average\":\"weighted\"}},{\"name\":\"f1_score\",\"params\":{\"average\":\"weighted\"}}]'", prefix="--metrics_info")
    behaviour_predictions_dir = Input("behaviour_predictions_dir", "string", "./data/behaviour", prefix="--npy_output_dir")
    area_table_output_format = Input("area_table_output_format", "string", "to_csv", prefix="--output_format")
    behaviour_table_output_format = Input("behaviour_table_output_format", "string", "to_csv", prefix="--output_format")
    pred_display_output_dir = Input("pred_display_output_dir", "string", "./metrics/area/displays", prefix="--pred_display_output_dir")
    pred_display_kwargs = Input("pred_display_kwargs", "string", "'{\"kind\":\"actual_vs_predicted\"}'", prefix="--display_kwargs")
    matrix_output_dir = Input("matrix_output_dir", "string", "./metrics/behaviour/displays", prefix="--matrix_output_dir")
    area_feature_outdir = Input("area_feature_outdir", "string", "./metrics/area/features", prefix="--output_dir")
    behaviour_feature_outdir = Input("behaviour_feature_outdir", "string", "./metrics/behaviour/features", prefix="--output_dir")


    # Define tasks
    preprocess = Task(name="preprocess",
                      base_command="/preprocess.sh",
                      stdout="preprocess.txt",
                      stderr="preprocess.err",
                      inputs=[Input("original_csv_path", "string", "./data/ucsd_fire_burned.csv", prefix="--original_csv_path"),
                              Input("encode_cols", "string", "fuels ignition safe_unsafe_fire_behavior", prefix="--encode_cols"),
                              Input("keep_cols", "string", "wind_speed wdir smois burned_area", prefix="--keep_cols"),
                              Input("encoder_name", "string", "OrdinalEncoder", prefix="--name"),
                              csv_path,
                              encoder_path],
                      outputs=[Output("preprocess_stdout", "stdout"),
                               Output("preprocess_stderr", "stderr", source="preprocess/preprocess_stderr"),
                               Output("cleaned_data", "File", glob="$(inputs.csv_path)"),
                               Output("encoder", "File", glob="$(inputs.encoder_path)")],
                      hints=[
                        Charliecloud(docker_file="Dockerfile.fire_analysis",
                            container_name="fire_analysis")
                        ])

    split_area = Task(name="split_area",
                      base_command="/split_data.sh",
                      stdout="split_area.txt",
                      stderr="split_area.err",
                      inputs=[csv_path,
                              area_features,
                              Input("area_target", "string", "burned_area", prefix="--target"),
                              test_size,
                              random_seed,
                              area_data_dir,
                              Input("preprocess_info", "File", value="preprocess/preprocess_stdout", prefix="--preprocess_info"),
                              data_scaler],
                      outputs=[Output("split_area_stdout", "stdout"),
                               Output("split_area_stderr", "stderr", source="split_area/split_area_stderr"),
                               Output("outdir", "Directory", glob="$(inputs.area_data_dir)/*_*.npy")],
                      hints=[
                        Charliecloud(docker_file="Dockerfile.fire_analysis",
                            container_name="fire_analysis")
                        ])

    split_behaviour = Task(name="split_behaviour",
                           base_command="/split_data.sh",
                           stdout="split_behaviour.txt",
                           stderr="split_behaviour.err",
                           inputs=[csv_path,
                                   behaviour_features,
                                   behaviour_target,
                                   test_size,
                                   random_seed,
                                   behaviour_data_dir,
                                   Input("preprocess_info", "File", value="preprocess/preprocess_stdout", prefix="--preprocess_info"),
                                   data_scaler],
                           outputs=[Output("split_behaviour_stdout", "stdout"),
                                    Output("split_behaviour_stderr", "stderr", source="split_behaviour/split_behaviour_stderr"),
                                    Output("outdir", "Directory", glob="$(inputs.behaviour_data_dir)/*_*.npy")],
                           hints=[
                                Charliecloud(docker_file="Dockerfile.fire_analysis",
                                    container_name="fire_analysis")
                                ])


    opt_rf_area = Task(name="opt_rf_area",
                       base_command="/optimize_models.sh",
                       stdout="opt_rf_area.txt",
                       stderr="opt_rf_area.err",
                       inputs=[area_data_dir,
                               rf_area_name,
                               Input("rf_area_sk_class", "string", "sklearn.ensemble.RandomForestRegressor", prefix="--sk_class"),
                               Input("rf_area_param_grid", "string", "'{\"max_depth\":[3,5,7,10,None],\"n_estimators\":[50,100,200,300,400,500],\"max_features\":[\"sqrt\",\"log2\",None],\"min_samples_leaf\":[1,2,4]}'", prefix="--param_grid"),
                               area_models_dir,
                               area_metrics_dir,
                               Input("split_area_info", "File", value="split_area/split_area_stdout", prefix="--split_info"),
                               Input("rf_area_kwargs", "string", "'{\"n_jobs\":1}'", prefix="--model_kwargs"),
                               common_gridsearch_kwargs],
                       outputs=[Output("opt_rf_area_stdout", "stdout"),
                                Output("opt_rf_area_stderr", "stderr", source="opt_rf_area/opt_rf_area_stderr"),
                                Output("opt_rf_area_model", "File", glob="$(inputs.area_models_dir)/$(inputs.rf_area_name).joblib"),
                                Output("opt_rf_area_json", "File", glob="$(inputs.area_metrics_dir)/$(inputs.rf_area_name).json"),
                                Output("opt_rf_area_cv", "File", glob="$(inputs.area_metrics_dir)/$(inputs.rf_area_name)_cv_results.csv")],
                       hints=[
                         Charliecloud(docker_file="Dockerfile.fire_analysis",
                             container_name="fire_analysis")
                         ])

    opt_rf_behaviour = Task(name="opt_rf_behaviour",
                            base_command="/optimize_models.sh",
                            stdout="opt_rf_behaviour.txt",
                            stderr="opt_rf_behaviour.err",
                            inputs=[behaviour_data_dir,
                                    rf_behaviour_name,
                                    Input("rf_behaviour_sk_class", "string", "sklearn.ensemble.RandomForestClassifier", prefix="--sk_class"),
                                    Input("rf_behaviour_param_grid", "string", "'{\"max_depth\":[3,5,7,10,None],\"n_estimators\":[50,100,200,300,400,500],\"max_features\":[\"sqrt\",\"log2\"],\"min_samples_leaf\":[1,2,4]}'", prefix="--param_grid"),
                                    behaviour_models_dir,
                                    behaviour_metrics_dir,
                                    Input("split_behaviour_info", "File", value="split_behaviour/split_behaviour_stdout", prefix="--split_info"),
                                    Input("rf_behaviour_kwargs", "string", "'{\"n_jobs\":1}'", prefix="--model_kwargs"),
                                    common_gridsearch_kwargs],
                            outputs=[Output("opt_rf_behaviour_stdout", "stdout"),
                                     Output("opt_rf_behaviour_stderr", "stderr", source="opt_rf_behaviour/opt_rf_behaviour_stderr"),
                                     Output("opt_rf_behaviour_model", "File", glob="$(inputs.behaviour_models_dir)/$(inputs.rf_behaviour_name).joblib"),
                                     Output("opt_rf_behaviour_json", "File", glob="$(inputs.behaviour_metrics_dir)/$(inputs.rf_behaviour_name).json"),
                                     Output("opt_rf_behaviour_cv", "File", glob="$(inputs.behaviour_metrics_dir)/$(inputs.rf_behaviour_name)_cv_results.csv")],
                            hints=[
                              Charliecloud(docker_file="Dockerfile.fire_analysis",
                                  container_name="fire_analysis")
                              ])

    eval_rf_area = Task(name="eval_rf_area",
                        base_command="/eval_models.sh",
                        stdout="eval_rf_area.txt",
                        stderr="eval_rf_area.err",
                        inputs=[area_data_dir,
                                area_models_dir,
                                rf_area_name,
                                area_metrics,
                                area_metrics_dir,
                                area_predictions_dir,
                                Input("opt_rf_area_info", "File", value="opt_rf_area/opt_rf_area_stdout", prefix="--opt_info")],
                        outputs=[Output("eval_rf_area_stdout", "stdout"),
                                 Output("eval_rf_area_stderr", "stderr", source="eval_rf_area/eval_rf_area_stderr"),
                                 Output("eval_rf_area_json", "File", glob="$(inputs.area_metrics_dir)/$(inputs.rf_area_name).json"),
                                 Output("eval_rf_area_pred", "File", glob="$(inputs.area_predictions_dir)/$(inputs.rf_area_name)_y_pred.npy")],
                        hints=[
                          Charliecloud(docker_file="Dockerfile.fire_analysis",
                              container_name="fire_analysis")
                          ])

    eval_rf_behaviour = Task(name="eval_rf_behaviour",
                             base_command="/eval_models.sh",
                             stdout="eval_rf_behaviour.txt",
                             stderr="eval_rf_behaviour.err",
                             inputs=[behaviour_data_dir,
                                     behaviour_models_dir,
                                     rf_behaviour_name,
                                     behaviour_metrics,
                                     behaviour_metrics_dir,
                                     behaviour_predictions_dir,
                                     Input("opt_rf_behaviour_info", "File", value="opt_rf_behaviour/opt_rf_behaviour_stdout", prefix="--opt_info")],
                             outputs=[Output("eval_rf_behaviour_stdout", "stdout"),
                                      Output("eval_rf_behaviour_stderr", "stderr", source="eval_rf_behaviour/eval_rf_behaviour_stderr"),
                                      Output("eval_rf_behaviour_json", "File", glob="$(inputs.behaviour_metrics_dir)/$(inputs.rf_behaviour_name).json"),
                                      Output("eval_rf_behaviour_pred", "File", glob="$(inputs.behaviour_predictions_dir)/$(inputs.rf_behaviour_name)_y_pred.npy")],
                             hints=[
                               Charliecloud(docker_file="Dockerfile.fire_analysis",
                                   container_name="fire_analysis")
                               ])


    create_area_table = Task(name="create_area_table",
                             base_command="/create_tables.sh",
                             stdout="create_area_table.txt",
                             stderr="create_area_table.err",
                             inputs=[Input("area_metrics_summary_dir", "string", "./metrics/area", prefix="--data_path"),
                                     area_table_output_format,
                                     Input("area_table_output_name", "string", "area_metrics_summary.csv", prefix="--output_name"),
                                     area_metrics_dir,
                                     Input("eval_info_rf", "File", value="eval_rf_area/eval_rf_area_stdout", prefix="--eval_info"),
                                     Input("area_table_output_kwargs", "string", "'{\"index\":False}'", prefix="--output_kwargs")],
                             outputs=[Output("create_area_table_stdout", "stdout"),
                                      Output("create_area_table_stderr", "stderr", source="create_area_table/create_area_table_stderr"),
                                      Output("area_table", "File", glob="$(inputs.area_metrics_dir)/$(inputs.area_table_output_name)")],
                             hints=[
                               Charliecloud(docker_file="Dockerfile.fire_analysis",
                                   container_name="fire_analysis")
                               ])

    create_behaviour_table = Task(name="create_behaviour_table",
                             base_command="/create_tables.sh",
                             stdout="create_behaviour_table.txt",
                             stderr="create_behaviour_table.err",
                             inputs=[Input("behaviour_metrics_summary_dir", "string", "./metrics/behaviour", prefix="--data_path"),
                                     behaviour_table_output_format,
                                     Input("behaviour_table_output_name", "string", "behaviour_metrics_summary.csv", prefix="--output_name"),
                                     behaviour_metrics_dir,
                                     Input("eval_info_rf", "File", value="eval_rf_behaviour/eval_rf_behaviour_stdout", prefix="--eval_info"),
                                     Input("behaviour_table_output_kwargs", "string", "'{\"index\":False}'", prefix="--output_kwargs")],
                             outputs=[Output("create_behaviour_table_stdout", "stdout"),
                                      Output("create_behaviour_table_stderr", "stderr", source="create_behaviour_table/create_behaviour_table_stderr"),
                                      Output("behaviour_table", "File", glob="$(inputs.behaviour_metrics_dir)/$(inputs.behaviour_table_output_name)")],
                             hints=[
                               Charliecloud(docker_file="Dockerfile.fire_analysis",
                                   container_name="fire_analysis")
                               ])

    pred_rf_display = Task(name="pred_rf_display",
                           base_command="/pred_display.sh",
                           stdout="pred_rf_display.txt",
                           stderr="pred_rf_display.err",
                           inputs=[area_data_dir,
                                   rf_area_name,
                                   pred_display_output_dir,
                                   pred_display_kwargs,
                                   Input("eval_info_rf", "File", value="eval_rf_area/eval_rf_area_stdout", prefix="--eval_info")],
                           outputs=[Output("pred_rf_display_stdout", "stdout"),
                                    Output("pred_rf_display_stderr", "stderr", source="pred_rf_display/pred_rf_display_stderr"),
                                    Output("pred_rf_display_png", "File", glob="$(inputs.pred_display_output_dir)/$(inputs.rf_area_name)_pred_err.png")],
                           hints=[
                             Charliecloud(docker_file="Dockerfile.fire_analysis",
                                 container_name="fire_analysis")
                             ])

    conf_rf = Task(name="conf_rf",
                   base_command="/confusion_matrix_maker.sh",
                   stdout="conf_rf.txt",
                   stderr="conf_rf.err",
                   inputs=[behaviour_data_dir,
                           encoder_path,
                           behaviour_target,
                           rf_behaviour_name,
                           matrix_output_dir,
                           Input("eval_info_rf", "File", value="eval_rf_behaviour/eval_rf_behaviour_stdout", prefix="--eval_info")],
                   outputs=[Output("conf_rf_stdout", "stdout"),
                            Output("conf_rf_stderr", "stderr", source="conf_rf/conf_rf_stderr"),
                            Output("conf_rf_matrix", "File", glob="$(inputs.matrix_output_dir)/$(inputs.rf_behaviour_name)_matrix.png")],
                   hints=[
                     Charliecloud(docker_file="Dockerfile.fire_analysis",
                         container_name="fire_analysis")
                     ])

    perm_rf_area = Task(name="perm_rf_area",
                        base_command="/feature_perm.sh",
                        stdout="perm_rf_area.txt",
                        stderr="perm_rf_area.err",
                        inputs=[area_data_dir,
                                area_models_dir,
                                rf_area_name,
                                area_features,
                                area_table_output_format,
                                Input("rf_area_dataframe_name", "string", "rf_area_features.csv", prefix="--dataframe_name"),
                                area_feature_outdir,
                                Input("opt_rf_area_info", "File", value="opt_rf_area/opt_rf_area_stdout", prefix="--opt_info")],
                        outputs=[Output("perm_rf_area_stdout", "stdout"),
                                 Output("perm_rf_area_stderr", "stderr", source="perm_rf_area/perm_rf_area_stderr"),
                                 Output("perm_rf_area_png", "File", glob="$(inputs.area_feature_outdir)/$(inputs.rf_area_name)_importances.png"),
                                 Output("perm_rf_area_table", "File", glob="$(inputs.area_feature_outdir)/$(inputs.rf_area_dataframe_name)")],
                        hints=[
                          Charliecloud(docker_file="Dockerfile.fire_analysis",
                              container_name="fire_analysis")
                          ])

    perm_rf_behaviour = Task(name="perm_rf_behaviour",
                        base_command="/feature_perm.sh",
                        stdout="perm_rf_behaviour.txt",
                        stderr="perm_rf_behaviour.err",
                        inputs=[behaviour_data_dir,
                                behaviour_models_dir,
                                rf_behaviour_name,
                                behaviour_features,
                                behaviour_table_output_format,
                                Input("rf_behaviour_dataframe_name", "string", "rf_behaviour_features.csv", prefix="--dataframe_name"),
                                behaviour_feature_outdir,
                                Input("opt_rf_behaviour_info", "File", value="opt_rf_behaviour/opt_rf_behaviour_stdout", prefix="--opt_info")],
                        outputs=[Output("perm_rf_behaviour_stdout", "stdout"),
                                 Output("perm_rf_behaviour_stderr", "stderr", source="perm_rf_behaviour/perm_rf_behaviour_stderr"),
                                 Output("perm_rf_behaviour_png", "File", glob="$(inputs.behaviour_feature_outdir)/$(inputs.rf_behaviour_name)_importances.png"),
                                 Output("perm_rf_behaviour_table", "File", glob="$(inputs.behaviour_feature_outdir)/$(inputs.rf_behaviour_dataframe_name)")],
                        hints=[
                          Charliecloud(docker_file="Dockerfile.fire_analysis",
                              container_name="fire_analysis")
                          ])


    workflow = Workflow("fire-workflow", [preprocess, split_area, split_behaviour, opt_rf_area, opt_rf_behaviour, eval_rf_area, eval_rf_behaviour, create_area_table, create_behaviour_table, pred_rf_display, conf_rf, perm_rf_area, perm_rf_behaviour])
    workflow.write_wf("fire-workflow")
    workflow.write_yaml("fire-workflow")


if __name__ == "__main__":
    main()

