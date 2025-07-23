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
    dt_area_name = Input("dt_area_name", "string", "decision_tree_regressor", prefix="--name")
    area_models_dir = Input("area_models_dir", "string", "./models/area", prefix="--model_dir_path")
    area_metrics_dir = Input("area_metrics_dir", "string", "./metrics/area", prefix="--metric_output_dir")
    common_gridsearch_kwargs = Input("common_gridsearch_kwargs", "string", "'{\"n_jobs\":-1,\"verbose\":3}'", prefix="--gridsearch_kwargs")
    rf_area_name = Input("rf_area_name", "string", "random_forest_regressor", prefix="--name")
    knn_area_name = Input("knn_area_name", "string", "k_neighbors_regressor", prefix="--name")
    svm_area_name = Input("svm_area_name", "string", "support_vector_regressor", prefix="--name")
    mlp_area_name = Input("mlp_area_name", "string", "mlp_regressor", prefix="--name")
    dt_behaviour_name = Input("dt_behaviour_name", "string", "decision_tree_classifier", prefix="--name")
    behaviour_models_dir = Input("behaviour_models_dir", "string", "./models/behaviour", prefix="--model_dir_path")
    behaviour_metrics_dir = Input("behaviour_metrics_dir", "string", "./metrics/behaviour", prefix="--metric_output_dir")
    rf_behaviour_name = Input("rf_behaviour_name", "string", "random_forest_classifier", prefix="--name")
    knn_behaviour_name = Input("knn_behaviour_name", "string", "k_neighbors_classifier", prefix="--name")
    svm_behaviour_name = Input("svm_behaviour_name", "string", "support_vector_classifier", prefix="--name")
    mlp_behaviour_name = Input("mlp_behaviour_name", "string", "mlp_classifier", prefix="--name")
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

    opt_dt_area = Task(name="opt_dt_area",
                       base_command="/optimize_models.sh",
                       stdout="opt_dt_area.txt",
                       stderr="opt_dt_area.err",
                       inputs=[area_data_dir,
                               dt_area_name,
                               Input("dt_area_sk_class", "string", "sklearn.tree.DecisionTreeRegressor", prefix="--sk_class"),
                               Input("dt_area_param_grid", "string", "'{\"splitter\":[\"best\",\"random\"],\"max_depth\":[1,3,5,7,9,11,12,None],\"min_samples_leaf\":[1,2,3,4,5,6,7,8,9,10],\"min_weight_fraction_leaf\":[0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9],\"max_features\":[\"auto\",\"log2\",\"sqrt\",None],\"max_leaf_nodes\":[None,10,20,30,40,50,60,70,80,90],\"criterion\":[\"poisson\",\"squared_error\"]}'", prefix="--param_grid"),
                               area_models_dir,
                               area_metrics_dir,
                               Input("split_area_info", "File", value="split_area/split_area_stdout", prefix="--split_info"),
                               common_gridsearch_kwargs],
                       outputs=[Output("opt_dt_area_stdout", "stdout"),
                                Output("opt_dt_area_stderr", "stderr", source="opt_dt_area/opt_dt_area_stderr"),
                                Output("opt_dt_area_model", "File", glob="$(inputs.area_models_dir)/$(inputs.dt_area_name).joblib"),
                                Output("opt_dt_area_json", "File", glob="$(inputs.area_metrics_dir)/$(inputs.dt_area_name).json"),
                                Output("opt_dt_area_cv", "File", glob="$(inputs.area_metrics_dir)/$(inputs.dt_area_name)_cv_results.csv")],
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

    opt_knn_area = Task(name="opt_knn_area",
                        base_command="/optimize_models.sh",
                        stdout="opt_knn_area.txt",
                        stderr="opt_knn_area.err",
                        inputs=[area_data_dir,
                                knn_area_name,
                                Input("knn_area_sk_class", "string", "sklearn.neighbors.KNeighborsRegressor", prefix="--sk_class"),
                                Input("knn_area_param_grid", "string", "'{\"n_neighbors\":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30],\"leaf_size\":[20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40],\"p\":[1,2],\"weights\":[\"uniform\",\"distance\"],\"metric\":[\"minkowski\",\"chebyshev\"]}'", prefix="--param_grid"),
                                area_models_dir,
                                area_metrics_dir,
                                Input("split_area_info", "File", value="split_area/split_area_stdout", prefix="--split_info"),
                                Input("knn_area_kwargs", "string", "'{\"n_jobs\":1}'", prefix="--model_kwargs"),
                                common_gridsearch_kwargs],
                        outputs=[Output("opt_knn_area_stdout", "stdout"),
                                 Output("opt_knn_area_stderr", "stderr", source="opt_knn_area/opt_knn_area_stderr"),
                                 Output("opt_knn_area_model", "File", glob="$(inputs.area_models_dir)/$(inputs.knn_area_name).joblib"),
                                 Output("opt_knn_area_json", "File", glob="$(inputs.area_metrics_dir)/$(inputs.knn_area_name).json"),
                                 Output("opt_knn_area_cv", "File", glob="$(inputs.area_metrics_dir)/$(inputs.knn_area_name)_cv_results.csv")],
                        hints=[
                          Charliecloud(docker_file="Dockerfile.fire_analysis",
                              container_name="fire_analysis")
                          ])

    opt_svm_area = Task(name="opt_svm_area",
                        base_command="/optimize_models.sh",
                        stdout="opt_svm_area.txt",
                        stderr="opt_svm_area.err",
                        inputs=[area_data_dir,
                                svm_area_name,
                                Input("svm_area_sk_class", "string", "sklearn.svm.SVR", prefix="--sk_class"),
                                Input("svm_area_param_grid", "string", "'{\"kernel\":[\"linear\",\"rbf\"],\"C\":[1,10,100,1000],\"gamma\":[1,0.1,0.001,0.0001,\"scale\"],\"degree\":[2,3],\"epsilon\":[0.01,0.1,0.5]}'", prefix="--param_grid"),
                                area_models_dir,
                                area_metrics_dir,
                                Input("split_area_info", "File", value="split_area/split_area_stdout", prefix="--split_info"),
                                common_gridsearch_kwargs],
                        outputs=[Output("opt_svm_area_stdout", "stdout"),
                                 Output("opt_svm_area_stderr", "stderr", source="opt_svm_area/opt_svm_area_stderr"),
                                 Output("opt_svm_area_model", "File", glob="$(inputs.area_models_dir)/$(inputs.svm_area_name).joblib"),
                                 Output("opt_svm_area_json", "File", glob="$(inputs.area_metrics_dir)/$(inputs.svm_area_name).json"),
                                 Output("opt_svm_area_cv", "File", glob="$(inputs.area_metrics_dir)/$(inputs.svm_area_name)_cv_results.csv")],
                        hints=[
                          Charliecloud(docker_file="Dockerfile.fire_analysis",
                              container_name="fire_analysis")
                          ])

    opt_mlp_area = Task(name="opt_mlp_area",
                        base_command="/optimize_models.sh",
                        stdout="opt_mlp_area.txt",
                        stderr="opt_mlp_area.err",
                        inputs=[area_data_dir,
                                mlp_area_name,
                                Input("mlp_area_sk_class", "string", "sklearn.neural_network.MLPRegressor", prefix="--sk_class"),
                                Input("mlp_area_param_grid", "string", "'{\"hidden_layer_sizes\":[(150,100,50),(120,80,40),(100,50,30)],\"max_iter\":[100,200,400,600,800,1000],\"activation\":[\"tanh\",\"relu\"],\"solver\":[\"sgd\",\"adam\"],\"alpha\":[0.0001,0.05],\"learning_rate\":[\"constant\",\"adaptive\"]}'", prefix="--param_grid"),
                                area_models_dir,
                                area_metrics_dir,
                                Input("split_area_info", "File", value="split_area/split_area_stdout", prefix="--split_info"),
                                common_gridsearch_kwargs],
                        outputs=[Output("opt_mlp_area_stdout", "stdout"),
                                 Output("opt_mlp_area_stderr", "stderr", source="opt_mlp_area/opt_mlp_area_stderr"),
                                 Output("opt_mlp_area_model", "File", glob="$(inputs.area_models_dir)/$(inputs.mlp_area_name).joblib"),
                                 Output("opt_mlp_area_json", "File", glob="$(inputs.area_metrics_dir)/$(inputs.mlp_area_name).json"),
                                 Output("opt_mlp_area_cv", "File", glob="$(inputs.area_metrics_dir)/$(inputs.mlp_area_name)_cv_results.csv")],
                        hints=[
                          Charliecloud(docker_file="Dockerfile.fire_analysis",
                              container_name="fire_analysis")
                          ])

    opt_dt_behaviour = Task(name="opt_dt_behaviour",
                            base_command="/optimize_models.sh",
                            stdout="opt_dt_behaviour.txt",
                            stderr="opt_dt_behaviour.err",
                            inputs=[behaviour_data_dir,
                                    dt_behaviour_name,
                                    Input("dt_behaviour_sk_class", "string", "sklearn.tree.DecisionTreeClassifier", prefix="--sk_class"),
                                    Input("dt_behaviour_param_grid", "string", "'{\"criterion\":[\"gini\",\"entropy\",\"log_loss\"],\"max_depth\":[1,3,5,7,9,11,12,None],\"min_samples_leaf\":[1,2,3,4,5,6,7,8,9,10],\"min_weight_fraction_leaf\":[0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9],\"max_features\":[\"log2\",\"sqrt\",None],\"max_leaf_nodes\":[None,10,20,30,40,50,60,70,80,90],\"ccp_alpha\":[0.0, 0.001, 0.01, 0.1]}'", prefix="--param_grid"),
                                    behaviour_models_dir,
                                    behaviour_metrics_dir,
                                    Input("split_behaviour_info", "File", value="split_behaviour/split_behaviour_stdout", prefix="--split_info"),
                                    common_gridsearch_kwargs],
                            outputs=[Output("opt_dt_behaviour_stdout", "stdout"),
                                     Output("opt_dt_behaviour_stderr", "stderr", source="opt_dt_behaviour/opt_dt_behaviour_stderr"),
                                     Output("opt_dt_behaviour_model", "File", glob="$(inputs.behaviour_models_dir)/$(inputs.dt_behaviour_name).joblib"),
                                     Output("opt_dt_behaviour_json", "File", glob="$(inputs.behaviour_metrics_dir)/$(inputs.dt_behaviour_name).json"),
                                     Output("opt_dt_behaviour_cv", "File", glob="$(inputs.behaviour_metrics_dir)/$(inputs.dt_behaviour_name)_cv_results.csv")],
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

    opt_knn_behaviour = Task(name="opt_knn_behaviour",
                             base_command="/optimize_models.sh",
                             stdout="opt_knn_behaviour.txt",
                             stderr="opt_knn_behaviour.err",
                             inputs=[behaviour_data_dir,
                                     knn_behaviour_name,
                                     Input("knn_behaviour_sk_class", "string", "sklearn.neighbors.KNeighborsClassifier", prefix="--sk_class"),
                                     Input("knn_behaviour_param_grid", "string", "'{\"n_neighbors\":[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30],\"leaf_size\":[20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40],\"p\":[1,2],\"weights\":[\"uniform\",\"distance\"],\"metric\":[\"minkowski\",\"chebyshev\"]}'", prefix="--param_grid"),
                                     behaviour_models_dir,
                                     behaviour_metrics_dir,
                                     Input("split_behaviour_info", "File", value="split_behaviour/split_behaviour_stdout", prefix="--split_info"),
                                     Input("knn_behaviour_kwargs", "string", "'{\"n_jobs\":1}'", prefix="--model_kwargs"),
                                     common_gridsearch_kwargs],
                             outputs=[Output("opt_knn_behaviour_stdout", "stdout"),
                                      Output("opt_knn_behaviour_stderr", "stderr", source="opt_knn_behaviour/opt_knn_behaviour_stderr"),
                                      Output("opt_knn_behaviour_model", "File", glob="$(inputs.behaviour_models_dir)/$(inputs.knn_behaviour_name).joblib"),
                                      Output("opt_knn_behaviour_json", "File", glob="$(inputs.behaviour_metrics_dir)/$(inputs.knn_behaviour_name).json"),
                                      Output("opt_knn_behaviour_cv", "File", glob="$(inputs.behaviour_metrics_dir)/$(inputs.knn_behaviour_name)_cv_results.csv")],
                             hints=[
                               Charliecloud(docker_file="Dockerfile.fire_analysis",
                                   container_name="fire_analysis")
                               ])

    opt_svm_behaviour = Task(name="opt_svm_behaviour",
                             base_command="/optimize_models.sh",
                             stdout="opt_svm_behaviour.txt",
                             stderr="opt_svm_behaviour.err",
                             inputs=[behaviour_data_dir,
                                     svm_behaviour_name,
                                     Input("svm_behaviour_sk_class", "string", "sklearn.svm.SVC", prefix="--sk_class"),
                                     Input("svm_behaviour_param_grid", "string", "'{\"kernel\":[\"linear\",\"rbf\"],\"C\":[1,10,100,1000],\"gamma\":[1,0.1,0.001,0.0001,\"scale\"]}'", prefix="--param_grid"),
                                     behaviour_models_dir,
                                     behaviour_metrics_dir,
                                     Input("split_behaviour_info", "File", value="split_behaviour/split_behaviour_stdout", prefix="--split_info"),
                                     common_gridsearch_kwargs],
                             outputs=[Output("opt_svm_behaviour_stdout", "stdout"),
                                      Output("opt_svm_behaviour_stderr", "stderr", source="opt_svm_behaviour/opt_svm_behaviour_stderr"),
                                      Output("opt_svm_behaviour_model", "File", glob="$(inputs.behaviour_models_dir)/$(inputs.svm_behaviour_name).joblib"),
                                      Output("opt_svm_behaviour_json", "File", glob="$(inputs.behaviour_metrics_dir)/$(inputs.svm_behaviour_name).json"),
                                      Output("opt_svm_behaviour_cv", "File", glob="$(inputs.behaviour_metrics_dir)/$(inputs.svm_behaviour_name)_cv_results.csv")],
                             hints=[
                               Charliecloud(docker_file="Dockerfile.fire_analysis",
                                   container_name="fire_analysis")
                               ])

    opt_mlp_behaviour = Task(name="opt_mlp_behaviour",
                             base_command="/optimize_models.sh",
                             stdout="opt_mlp_behaviour.txt",
                             stderr="opt_mlp_behaviour.err",
                             inputs=[behaviour_data_dir,
                                     mlp_behaviour_name,
                                     Input("mlp_behaviour_sk_class", "string", "sklearn.neural_network.MLPClassifier", prefix="--sk_class"),
                                     Input("mlp_behaviour_param_grid", "string", "'{\"hidden_layer_sizes\":[(150,100,50),(120,80,40),(100,50,30)],\"max_iter\":[100,200,400,600,800,1000],\"activation\":[\"tanh\",\"relu\"],\"solver\":[\"sgd\",\"adam\"],\"alpha\":[0.0001,0.05],\"learning_rate\":[\"constant\",\"adaptive\"]}'", prefix="--param_grid"),
                                     behaviour_models_dir,
                                     behaviour_metrics_dir,
                                     Input("split_behaviour_info", "File", value="split_behaviour/split_behaviour_stdout", prefix="--split_info"),
                                     common_gridsearch_kwargs],
                             outputs=[Output("opt_mlp_behaviour_stdout", "stdout"),
                                      Output("opt_mlp_behaviour_stderr", "stderr", source="opt_mlp_behaviour/opt_mlp_behaviour_stderr"),
                                      Output("opt_mlp_behaviour_model", "File", glob="$(inputs.behaviour_models_dir)/$(inputs.mlp_behaviour_name).joblib"),
                                      Output("opt_mlp_behaviour_json", "File", glob="$(inputs.behaviour_metrics_dir)/$(inputs.mlp_behaviour_name).json"),
                                      Output("opt_mlp_behaviour_cv", "File", glob="$(inputs.behaviour_metrics_dir)/$(inputs.mlp_behaviour_name)_cv_results.csv")],
                             hints=[
                               Charliecloud(docker_file="Dockerfile.fire_analysis",
                                   container_name="fire_analysis")
                               ])

    eval_dt_area = Task(name="eval_dt_area",
                        base_command="/eval_models.sh",
                        stdout="eval_dt_area.txt",
                        stderr="eval_dt_area.err",
                        inputs=[area_data_dir,
                                area_models_dir,
                                dt_area_name,
                                area_metrics,
                                area_metrics_dir,
                                area_predictions_dir,
                                Input("opt_dt_area_info", "File", value="opt_dt_area/opt_dt_area_stdout", prefix="--opt_info")],
                        outputs=[Output("eval_dt_area_stdout", "stdout"),
                                 Output("eval_dt_area_stderr", "stderr", source="eval_dt_area/eval_dt_area_stderr"),
                                 Output("eval_dt_area_json", "File", glob="$(inputs.area_metrics_dir)/$(inputs.dt_area_name).json"),
                                 Output("eval_dt_area_pred", "File", glob="$(inputs.area_predictions_dir)/$(inputs.dt_area_name)_y_pred.npy")],
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

    eval_knn_area = Task(name="eval_knn_area",
                         base_command="/eval_models.sh",
                         stdout="eval_knn_area.txt",
                         stderr="eval_knn_area.err",
                         inputs=[area_data_dir,
                                 area_models_dir,
                                 knn_area_name,
                                 area_metrics,
                                 area_metrics_dir,
                                 area_predictions_dir,
                                 Input("opt_knn_area_info", "File", value="opt_knn_area/opt_knn_area_stdout", prefix="--opt_info")],
                         outputs=[Output("eval_knn_area_stdout", "stdout"),
                                  Output("eval_knn_area_stderr", "stderr", source="eval_knn_area/eval_knn_area_stderr"),
                                  Output("eval_knn_area_json", "File", glob="$(inputs.area_metrics_dir)/$(inputs.knn_area_name).json"),
                                  Output("eval_knn_area_pred", "File", glob="$(inputs.area_predictions_dir)/$(inputs.knn_area_name)_y_pred.npy")],
                         hints=[
                           Charliecloud(docker_file="Dockerfile.fire_analysis",
                               container_name="fire_analysis")
                           ])

    eval_svm_area = Task(name="eval_svm_area",
                         base_command="/eval_models.sh",
                         stdout="eval_svm_area.txt",
                         stderr="eval_svm_area.err",
                         inputs=[area_data_dir,
                                 area_models_dir,
                                 svm_area_name,
                                 area_metrics,
                                 area_metrics_dir,
                                 area_predictions_dir,
                                 Input("opt_svm_area_info", "File", value="opt_svm_area/opt_svm_area_stdout", prefix="--opt_info")],
                         outputs=[Output("eval_svm_area_stdout", "stdout"),
                                  Output("eval_svm_area_stderr", "stderr", source="eval_svm_area/eval_svm_area_stderr"),
                                  Output("eval_svm_area_json", "File", glob="$(inputs.area_metrics_dir)/$(inputs.svm_area_name).json"),
                                  Output("eval_svm_area_pred", "File", glob="$(inputs.area_predictions_dir)/$(inputs.svm_area_name)_y_pred.npy")],
                         hints=[
                           Charliecloud(docker_file="Dockerfile.fire_analysis",
                               container_name="fire_analysis")
                           ])

    eval_mlp_area = Task(name="eval_mlp_area",
                         base_command="/eval_models.sh",
                         stdout="eval_mlp_area.txt",
                         stderr="eval_mlp_area.err",
                         inputs=[area_data_dir,
                                 area_models_dir,
                                 mlp_area_name,
                                 area_metrics,
                                 area_metrics_dir,
                                 area_predictions_dir,
                                 Input("opt_mlp_area_info", "File", value="opt_mlp_area/opt_mlp_area_stdout", prefix="--opt_info")],
                         outputs=[Output("eval_mlp_area_stdout", "stdout"),
                                  Output("eval_mlp_area_stderr", "stderr", source="eval_mlp_area/eval_mlp_area_stderr"),
                                  Output("eval_mlp_area_json", "File", glob="$(inputs.area_metrics_dir)/$(inputs.mlp_area_name).json"),
                                  Output("eval_mlp_area_pred", "File", glob="$(inputs.area_predictions_dir)/$(inputs.mlp_area_name)_y_pred.npy")],
                         hints=[
                           Charliecloud(docker_file="Dockerfile.fire_analysis",
                               container_name="fire_analysis")
                           ])

    eval_dt_behaviour = Task(name="eval_dt_behaviour",
                             base_command="/eval_models.sh",
                             stdout="eval_dt_behaviour.txt",
                             stderr="eval_dt_behaviour.err",
                             inputs=[behaviour_data_dir,
                                     behaviour_models_dir,
                                     dt_behaviour_name,
                                     behaviour_metrics,
                                     behaviour_metrics_dir,
                                     behaviour_predictions_dir,
                                     Input("opt_dt_behaviour_info", "File", value="opt_dt_behaviour/opt_dt_behaviour_stdout", prefix="--opt_info")],
                             outputs=[Output("eval_dt_behaviour_stdout", "stdout"),
                                      Output("eval_dt_behaviour_stderr", "stderr", source="eval_dt_behaviour/eval_dt_behaviour_stderr"),
                                      Output("eval_dt_behaviour_json", "File", glob="$(inputs.behaviour_metrics_dir)/$(inputs.dt_behaviour_name).json"),
                                      Output("eval_dt_behaviour_pred", "File", glob="$(inputs.behaviour_predictions_dir)/$(inputs.dt_behaviour_name)_y_pred.npy")],
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

    eval_knn_behaviour = Task(name="eval_knn_behaviour",
                              base_command="/eval_models.sh",
                              stdout="eval_knn_behaviour.txt",
                              stderr="eval_knn_behaviour.err",
                              inputs=[behaviour_data_dir,
                                      behaviour_models_dir,
                                      knn_behaviour_name,
                                      behaviour_metrics,
                                      behaviour_metrics_dir,
                                      behaviour_predictions_dir,
                                      Input("opt_knn_behaviour_info", "File", value="opt_knn_behaviour/opt_knn_behaviour_stdout", prefix="--opt_info")],
                              outputs=[Output("eval_knn_behaviour_stdout", "stdout"),
                                       Output("eval_knn_behaviour_stderr", "stderr", source="eval_knn_behaviour/eval_knn_behaviour_stderr"),
                                       Output("eval_knn_behaviour_json", "File", glob="$(inputs.behaviour_metrics_dir)/$(inputs.knn_behaviour_name).json"),
                                       Output("eval_knn_behaviour_pred", "File", glob="$(inputs.behaviour_predictions_dir)/$(inputs.knn_behaviour_name)_y_pred.npy")],
                              hints=[
                                Charliecloud(docker_file="Dockerfile.fire_analysis",
                                    container_name="fire_analysis")
                                ])

    eval_svm_behaviour = Task(name="eval_svm_behaviour",
                              base_command="/eval_models.sh",
                              stdout="eval_svm_behaviour.txt",
                              stderr="eval_svm_behaviour.err",
                              inputs=[behaviour_data_dir,
                                      behaviour_models_dir,
                                      svm_behaviour_name,
                                      behaviour_metrics,
                                      behaviour_metrics_dir,
                                      behaviour_predictions_dir,
                                      Input("opt_svm_behaviour_info", "File", value="opt_svm_behaviour/opt_svm_behaviour_stdout", prefix="--opt_info")],
                              outputs=[Output("eval_svm_behaviour_stdout", "stdout"),
                                       Output("eval_svm_behaviour_stderr", "stderr", source="eval_svm_behaviour/eval_svm_behaviour_stderr"),
                                       Output("eval_svm_behaviour_json", "File", glob="$(inputs.behaviour_metrics_dir)/$(inputs.svm_behaviour_name).json"),
                                       Output("eval_svm_behaviour_pred", "File", glob="$(inputs.behaviour_predictions_dir)/$(inputs.svm_behaviour_name)_y_pred.npy")],
                              hints=[
                                Charliecloud(docker_file="Dockerfile.fire_analysis",
                                    container_name="fire_analysis")
                                ])

    eval_mlp_behaviour = Task(name="eval_mlp_behaviour",
                              base_command="/eval_models.sh",
                              stdout="eval_mlp_behaviour.txt",
                              stderr="eval_mlp_behaviour.err",
                              inputs=[behaviour_data_dir,
                                      behaviour_models_dir,
                                      mlp_behaviour_name,
                                      behaviour_metrics,
                                      behaviour_metrics_dir,
                                      behaviour_predictions_dir,
                                      Input("opt_mlp_behaviour_info", "File", value="opt_mlp_behaviour/opt_mlp_behaviour_stdout", prefix="--opt_info")],
                              outputs=[Output("eval_mlp_behaviour_stdout", "stdout"),
                                       Output("eval_mlp_behaviour_stderr", "stderr", source="eval_mlp_behaviour/eval_mlp_behaviour_stderr"),
                                       Output("eval_mlp_behaviour_json", "File", glob="$(inputs.behaviour_metrics_dir)/$(inputs.mlp_behaviour_name).json"),
                                       Output("eval_mlp_behaviour_pred", "File", glob="$(inputs.behaviour_predictions_dir)/$(inputs.mlp_behaviour_name)_y_pred.npy")],
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
                                     Input("eval_info_dt", "File", value="eval_dt_area/eval_dt_area_stdout", prefix="--eval_info"),
                                     Input("eval_info_rf", "File", value="eval_rf_area/eval_rf_area_stdout", prefix="--eval_info"),
                                     Input("eval_info_knn", "File", value="eval_knn_area/eval_knn_area_stdout", prefix="--eval_info"),
                                     Input("eval_info_svm", "File", value="eval_svm_area/eval_svm_area_stdout", prefix="--eval_info"),
                                     Input("eval_info_mlp", "File", value="eval_mlp_area/eval_mlp_area_stdout", prefix="--eval_info"),
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
                                     Input("eval_info_dt", "File", value="eval_dt_behaviour/eval_dt_behaviour_stdout", prefix="--eval_info"),
                                     Input("eval_info_rf", "File", value="eval_rf_behaviour/eval_rf_behaviour_stdout", prefix="--eval_info"),
                                     Input("eval_info_knn", "File", value="eval_knn_behaviour/eval_knn_behaviour_stdout", prefix="--eval_info"),
                                     Input("eval_info_svm", "File", value="eval_svm_behaviour/eval_svm_behaviour_stdout", prefix="--eval_info"),
                                     Input("eval_info_mlp", "File", value="eval_mlp_behaviour/eval_mlp_behaviour_stdout", prefix="--eval_info"),
                                     Input("behaviour_table_output_kwargs", "string", "'{\"index\":False}'", prefix="--output_kwargs")],
                             outputs=[Output("create_behaviour_table_stdout", "stdout"),
                                      Output("create_behaviour_table_stderr", "stderr", source="create_behaviour_table/create_behaviour_table_stderr"),
                                      Output("behaviour_table", "File", glob="$(inputs.behaviour_metrics_dir)/$(inputs.behaviour_table_output_name)")],
                             hints=[
                               Charliecloud(docker_file="Dockerfile.fire_analysis",
                                   container_name="fire_analysis")
                               ])

    pred_dt_display = Task(name="pred_dt_display",
                           base_command="/pred_display.sh",
                           stdout="pred_dt_display.txt",
                           stderr="pred_dt_display.err",
                           inputs=[area_data_dir,
                                   dt_area_name,
                                   pred_display_output_dir,
                                   pred_display_kwargs,
                                   Input("eval_info_dt", "File", value="eval_dt_area/eval_dt_area_stdout", prefix="--eval_info")],
                           outputs=[Output("pred_dt_display_stdout", "stdout"),
                                    Output("pred_dt_display_stderr", "stderr", source="pred_dt_display/pred_dt_display_stderr"),
                                    Output("pred_dt_display_png", "File", glob="$(inputs.pred_display_output_dir)/$(inputs.dt_area_name)_pred_err.png")],
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

    pred_knn_display = Task(name="pred_knn_display",
                            base_command="/pred_display.sh",
                            stdout="pred_knn_display.txt",
                            stderr="pred_knn_display.err",
                            inputs=[area_data_dir,
                                    knn_area_name,
                                    pred_display_output_dir,
                                    pred_display_kwargs,
                                    Input("eval_info_knn", "File", value="eval_knn_area/eval_knn_area_stdout", prefix="--eval_info")],
                            outputs=[Output("pred_knn_display_stdout", "stdout"),
                                     Output("pred_knn_display_stderr", "stderr", source="pred_knn_display/pred_knn_display_stderr"),
                                     Output("pred_knn_display_png", "File", glob="$(inputs.pred_display_output_dir)/$(inputs.knn_area_name)_pred_err.png")],
                            hints=[
                              Charliecloud(docker_file="Dockerfile.fire_analysis",
                                  container_name="fire_analysis")
                              ])

    pred_svm_display = Task(name="pred_svm_display",
                            base_command="/pred_display.sh",
                            stdout="pred_svm_display.txt",
                            stderr="pred_svm_display.err",
                            inputs=[area_data_dir,
                                    svm_area_name,
                                    pred_display_output_dir,
                                    pred_display_kwargs,
                                    Input("eval_info_svm", "File", value="eval_svm_area/eval_svm_area_stdout", prefix="--eval_info")],
                            outputs=[Output("pred_svm_display_stdout", "stdout"),
                                     Output("pred_svm_display_stderr", "stderr", source="pred_svm_display/pred_svm_display_stderr"),
                                     Output("pred_svm_display_png", "File", glob="$(inputs.pred_display_output_dir)/$(inputs.svm_area_name)_pred_err.png")],
                            hints=[
                              Charliecloud(docker_file="Dockerfile.fire_analysis",
                                  container_name="fire_analysis")
                              ])

    pred_mlp_display = Task(name="pred_mlp_display",
                            base_command="/pred_display.sh",
                            stdout="pred_mlp_display.txt",
                            stderr="pred_mlp_display.err",
                            inputs=[area_data_dir,
                                    mlp_area_name,
                                    pred_display_output_dir,
                                    pred_display_kwargs,
                                    Input("eval_info_mlp", "File", value="eval_mlp_area/eval_mlp_area_stdout", prefix="--eval_info")],
                            outputs=[Output("pred_mlp_display_stdout", "stdout"),
                                     Output("pred_mlp_display_stderr", "stderr", source="pred_mlp_display/pred_mlp_display_stderr"),
                                     Output("pred_mlp_display_png", "File", glob="$(inputs.pred_display_output_dir)/$(inputs.mlp_area_name)_pred_err.png")],
                            hints=[
                              Charliecloud(docker_file="Dockerfile.fire_analysis",
                                  container_name="fire_analysis")
                              ])

    conf_dt = Task(name="conf_dt",
                   base_command="/confusion_matrix_maker.sh",
                   stdout="conf_dt.txt",
                   stderr="conf_dt.err",
                   inputs=[behaviour_data_dir,
                           encoder_path,
                           behaviour_target,
                           dt_behaviour_name,
                           matrix_output_dir,
                           Input("eval_info_dt", "File", value="eval_dt_behaviour/eval_dt_behaviour_stdout", prefix="--eval_info")],
                   outputs=[Output("conf_dt_stdout", "stdout"),
                            Output("conf_dt_stderr", "stderr", source="conf_dt/conf_dt_stderr"),
                            Output("conf_dt_matrix", "File", glob="$(inputs.matrix_output_dir)/$(inputs.dt_behaviour_name)_matrix.png")],
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

    conf_knn = Task(name="conf_knn",
                    base_command="/confusion_matrix_maker.sh",
                    stdout="conf_knn.txt",
                    stderr="conf_knn.err",
                    inputs=[behaviour_data_dir,
                            encoder_path,
                            behaviour_target,
                            knn_behaviour_name,
                            matrix_output_dir,
                            Input("eval_info_knn", "File", value="eval_knn_behaviour/eval_knn_behaviour_stdout", prefix="--eval_info")],
                    outputs=[Output("conf_knn_stdout", "stdout"),
                             Output("conf_knn_stderr", "stderr", source="conf_knn/conf_knn_stderr"),
                             Output("conf_knn_matrix", "File", glob="$(inputs.matrix_output_dir)/$(inputs.knn_behaviour_name)_matrix.png")],
                    hints=[
                      Charliecloud(docker_file="Dockerfile.fire_analysis",
                          container_name="fire_analysis")
                      ])

    conf_svm = Task(name="conf_svm",
                    base_command="/confusion_matrix_maker.sh",
                    stdout="conf_svm.txt",
                    stderr="conf_svm.err",
                    inputs=[behaviour_data_dir,
                            encoder_path,
                            behaviour_target,
                            svm_behaviour_name,
                            matrix_output_dir,
                            Input("eval_info_svm", "File", value="eval_svm_behaviour/eval_svm_behaviour_stdout", prefix="--eval_info")],
                    outputs=[Output("conf_svm_stdout", "stdout"),
                             Output("conf_svm_stderr", "stderr", source="conf_svm/conf_svm_stderr"),
                             Output("conf_svm_matrix", "File", glob="$(inputs.matrix_output_dir)/$(inputs.svm_behaviour_name)_matrix.png")],
                    hints=[
                      Charliecloud(docker_file="Dockerfile.fire_analysis",
                          container_name="fire_analysis")
                      ])

    conf_mlp = Task(name="conf_mlp",
                    base_command="/confusion_matrix_maker.sh",
                    stdout="conf_mlp.txt",
                    stderr="conf_mlp.err",
                    inputs=[behaviour_data_dir,
                            encoder_path,
                            behaviour_target,
                            mlp_behaviour_name,
                            matrix_output_dir,
                            Input("eval_info_mlp", "File", value="eval_mlp_behaviour/eval_mlp_behaviour_stdout", prefix="--eval_info")],
                    outputs=[Output("conf_mlp_stdout", "stdout"),
                             Output("conf_mlp_stderr", "stderr", source="conf_mlp/conf_mlp_stderr"),
                             Output("conf_mlp_matrix", "File", glob="$(inputs.matrix_output_dir)/$(inputs.mlp_behaviour_name)_matrix.png")],
                    hints=[
                      Charliecloud(docker_file="Dockerfile.fire_analysis",
                          container_name="fire_analysis")
                      ])

    perm_dt_area = Task(name="perm_dt_area",
                        base_command="/feature_perm.sh",
                        stdout="perm_dt_area.txt",
                        stderr="perm_dt_area.err",
                        inputs=[area_data_dir,
                                area_models_dir,
                                dt_area_name,
                                area_features,
                                area_table_output_format,
                                Input("dt_area_dataframe_name", "string", "dt_area_features.csv", prefix="--dataframe_name"),
                                area_feature_outdir,
                                Input("opt_dt_area_info", "File", value="opt_dt_area/opt_dt_area_stdout", prefix="--opt_info")],
                        outputs=[Output("perm_dt_area_stdout", "stdout"),
                                 Output("perm_dt_area_stderr", "stderr", source="perm_dt_area/perm_dt_area_stderr"),
                                 Output("perm_dt_area_png", "File", glob="$(inputs.area_feature_outdir)/$(inputs.dt_area_name)_importances.png"),
                                 Output("perm_dt_area_table", "File", glob="$(inputs.area_feature_outdir)/$(inputs.dt_area_dataframe_name)")],
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

    perm_knn_area = Task(name="perm_knn_area",
                         base_command="/feature_perm.sh",
                         stdout="perm_knn_area.txt",
                         stderr="perm_knn_area.err",
                         inputs=[area_data_dir,
                                 area_models_dir,
                                 knn_area_name,
                                 area_features,
                                 area_table_output_format,
                                 Input("knn_area_dataframe_name", "string", "knn_area_features.csv", prefix="--dataframe_name"),
                                 area_feature_outdir,
                                 Input("opt_knn_area_info", "File", value="opt_knn_area/opt_knn_area_stdout", prefix="--opt_info")],
                         outputs=[Output("perm_knn_area_stdout", "stdout"),
                                  Output("perm_knn_area_stderr", "stderr", source="perm_knn_area/perm_knn_area_stderr"),
                                  Output("perm_knn_area_png", "File", glob="$(inputs.area_feature_outdir)/$(inputs.knn_area_name)_importances.png"),
                                  Output("perm_knn_area_table", "File", glob="$(inputs.area_feature_outdir)/$(inputs.knn_area_dataframe_name)")],
                         hints=[
                           Charliecloud(docker_file="Dockerfile.fire_analysis",
                               container_name="fire_analysis")
                           ])

    perm_svm_area = Task(name="perm_svm_area",
                         base_command="/feature_perm.sh",
                         stdout="perm_svm_area.txt",
                         stderr="perm_svm_area.err",
                         inputs=[area_data_dir,
                                 area_models_dir,
                                 svm_area_name,
                                 area_features,
                                 area_table_output_format,
                                 Input("svm_area_dataframe_name", "string", "svm_area_features.csv", prefix="--dataframe_name"),
                                 area_feature_outdir,
                                 Input("opt_svm_area_info", "File", value="opt_svm_area/opt_svm_area_stdout", prefix="--opt_info")],
                         outputs=[Output("perm_svm_area_stdout", "stdout"),
                                  Output("perm_svm_area_stderr", "stderr", source="perm_svm_area/perm_svm_area_stderr"),
                                  Output("perm_svm_area_png", "File", glob="$(inputs.area_feature_outdir)/$(inputs.svm_area_name)_importances.png"),
                                  Output("perm_svm_area_table", "File", glob="$(inputs.area_feature_outdir)/$(inputs.svm_area_dataframe_name)")],
                         hints=[
                           Charliecloud(docker_file="Dockerfile.fire_analysis",
                               container_name="fire_analysis")
                           ])

    perm_mlp_area = Task(name="perm_mlp_area",
                         base_command="/feature_perm.sh",
                         stdout="perm_mlp_area.txt",
                         stderr="perm_mlp_area.err",
                         inputs=[area_data_dir,
                                 area_models_dir,
                                 mlp_area_name,
                                 area_features,
                                 area_table_output_format,
                                 Input("mlp_area_dataframe_name", "string", "mlp_area_features.csv", prefix="--dataframe_name"),
                                 area_feature_outdir,
                                 Input("opt_mlp_area_info", "File", value="opt_mlp_area/opt_mlp_area_stdout", prefix="--opt_info")],
                         outputs=[Output("perm_mlp_area_stdout", "stdout"),
                                  Output("perm_mlp_area_stderr", "stderr", source="perm_mlp_area/perm_mlp_area_stderr"),
                                  Output("perm_mlp_area_png", "File", glob="$(inputs.area_feature_outdir)/$(inputs.mlp_area_name)_importances.png"),
                                  Output("perm_mlp_area_table", "File", glob="$(inputs.area_feature_outdir)/$(inputs.mlp_area_dataframe_name)")],
                         hints=[
                           Charliecloud(docker_file="Dockerfile.fire_analysis",
                               container_name="fire_analysis")
                           ])

    perm_dt_behaviour = Task(name="perm_dt_behaviour",
                        base_command="/feature_perm.sh",
                        stdout="perm_dt_behaviour.txt",
                        stderr="perm_dt_behaviour.err",
                        inputs=[behaviour_data_dir,
                                behaviour_models_dir,
                                dt_behaviour_name,
                                behaviour_features,
                                behaviour_table_output_format,
                                Input("dt_behaviour_dataframe_name", "string", "dt_behaviour_features.csv", prefix="--dataframe_name"),
                                behaviour_feature_outdir,
                                Input("opt_dt_behaviour_info", "File", value="opt_dt_behaviour/opt_dt_behaviour_stdout", prefix="--opt_info")],
                        outputs=[Output("perm_dt_behaviour_stdout", "stdout"),
                                 Output("perm_dt_behaviour_stderr", "stderr", source="perm_dt_behaviour/perm_dt_behaviour_stderr"),
                                 Output("perm_dt_behaviour_png", "File", glob="$(inputs.behaviour_feature_outdir)/$(inputs.dt_behaviour_name)_importances.png"),
                                 Output("perm_dt_behaviour_table", "File", glob="$(inputs.behaviour_feature_outdir)/$(inputs.dt_behaviour_dataframe_name)")],
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

    perm_knn_behaviour = Task(name="perm_knn_behaviour",
                         base_command="/feature_perm.sh",
                         stdout="perm_knn_behaviour.txt",
                         stderr="perm_knn_behaviour.err",
                         inputs=[behaviour_data_dir,
                                 behaviour_models_dir,
                                 knn_behaviour_name,
                                 behaviour_features,
                                 behaviour_table_output_format,
                                 Input("knn_behaviour_dataframe_name", "string", "knn_behaviour_features.csv", prefix="--dataframe_name"),
                                 behaviour_feature_outdir,
                                 Input("opt_knn_behaviour_info", "File", value="opt_knn_behaviour/opt_knn_behaviour_stdout", prefix="--opt_info")],
                         outputs=[Output("perm_knn_behaviour_stdout", "stdout"),
                                  Output("perm_knn_behaviour_stderr", "stderr", source="perm_knn_behaviour/perm_knn_behaviour_stderr"),
                                  Output("perm_knn_behaviour_png", "File", glob="$(inputs.behaviour_feature_outdir)/$(inputs.knn_behaviour_name)_importances.png"),
                                  Output("perm_knn_behaviour_table", "File", glob="$(inputs.behaviour_feature_outdir)/$(inputs.knn_behaviour_dataframe_name)")],
                         hints=[
                           Charliecloud(docker_file="Dockerfile.fire_analysis",
                               container_name="fire_analysis")
                           ])

    perm_svm_behaviour = Task(name="perm_svm_behaviour",
                         base_command="/feature_perm.sh",
                         stdout="perm_svm_behaviour.txt",
                         stderr="perm_svm_behaviour.err",
                         inputs=[behaviour_data_dir,
                                 behaviour_models_dir,
                                 svm_behaviour_name,
                                 behaviour_features,
                                 behaviour_table_output_format,
                                 Input("svm_behaviour_dataframe_name", "string", "svm_behaviour_features.csv", prefix="--dataframe_name"),
                                 behaviour_feature_outdir,
                                 Input("opt_svm_behaviour_info", "File", value="opt_svm_behaviour/opt_svm_behaviour_stdout", prefix="--opt_info")],
                         outputs=[Output("perm_svm_behaviour_stdout", "stdout"),
                                  Output("perm_svm_behaviour_stderr", "stderr", source="perm_svm_behaviour/perm_svm_behaviour_stderr"),
                                  Output("perm_svm_behaviour_png", "File", glob="$(inputs.behaviour_feature_outdir)/$(inputs.svm_behaviour_name)_importances.png"),
                                  Output("perm_svm_behaviour_table", "File", glob="$(inputs.behaviour_feature_outdir)/$(inputs.svm_behaviour_dataframe_name)")],
                         hints=[
                           Charliecloud(docker_file="Dockerfile.fire_analysis",
                               container_name="fire_analysis")
                           ])

    perm_mlp_behaviour = Task(name="perm_mlp_behaviour",
                         base_command="/feature_perm.sh",
                         stdout="perm_mlp_behaviour.txt",
                         stderr="perm_mlp_behaviour.err",
                         inputs=[behaviour_data_dir,
                                 behaviour_models_dir,
                                 mlp_behaviour_name,
                                 behaviour_features,
                                 behaviour_table_output_format,
                                 Input("mlp_behaviour_dataframe_name", "string", "mlp_behaviour_features.csv", prefix="--dataframe_name"),
                                 behaviour_feature_outdir,
                                 Input("opt_mlp_behaviour_info", "File", value="opt_mlp_behaviour/opt_mlp_behaviour_stdout", prefix="--opt_info")],
                         outputs=[Output("perm_mlp_behaviour_stdout", "stdout"),
                                  Output("perm_mlp_behaviour_stderr", "stderr", source="perm_mlp_behaviour/perm_mlp_behaviour_stderr"),
                                  Output("perm_mlp_behaviour_png", "File", glob="$(inputs.behaviour_feature_outdir)/$(inputs.mlp_behaviour_name)_importances.png"),
                                  Output("perm_mlp_behaviour_table", "File", glob="$(inputs.behaviour_feature_outdir)/$(inputs.mlp_behaviour_dataframe_name)")],
                         hints=[
                           Charliecloud(docker_file="Dockerfile.fire_analysis",
                               container_name="fire_analysis")
                           ])


    workflow = Workflow("fire-workflow", [preprocess, split_area, split_behaviour, opt_dt_area, opt_rf_area, opt_knn_area, opt_svm_area, opt_mlp_area, opt_dt_behaviour, opt_rf_behaviour, opt_knn_behaviour, opt_svm_behaviour, opt_mlp_behaviour, eval_dt_area, eval_rf_area, eval_knn_area, eval_svm_area, eval_mlp_area, eval_dt_behaviour, eval_rf_behaviour, eval_knn_behaviour, eval_svm_behaviour, eval_mlp_behaviour, create_area_table, create_behaviour_table, pred_dt_display, pred_rf_display, pred_knn_display, pred_svm_display, pred_mlp_display, conf_dt, conf_rf, conf_knn, conf_svm, conf_mlp, perm_dt_area, perm_rf_area, perm_knn_area, perm_svm_area, perm_mlp_area, perm_dt_behaviour, perm_rf_behaviour, perm_knn_behaviour, perm_svm_behaviour, perm_mlp_behaviour])
    workflow.write_wf("fire-workflow")
    workflow.write_yaml("fire-workflow")


if __name__ == "__main__":
    main()

