// ==============================================================================
// ClearRoute Power Query (M) Automated Import Scripts
// Instructions:
// 1. In Power BI Desktop, click Home -> Transform Data.
// 2. Click Home -> Manage Parameters -> New Parameter.
//    Name: ExportFolderPath, Type: Text, Current Value: "C:\Users\aurian\Downloads\clear-route-main\powerbi\exports"
// 3. For each table, create a Blank Query, open Advanced Editor, and paste the code block.
// ==============================================================================

// ------------------------------------------------------------------------------
// TABLE 1: dim_location
// ------------------------------------------------------------------------------
let
    Source = Csv.Document(File.Contents(ExportFolderPath & "\dim_location.csv"), [Delimiter=",", Columns=11, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangedTypes = Table.TransformColumnTypes(PromotedHeaders, {
        {"location_id", type text},
        {"location_name", type text},
        {"city", type text},
        {"latitude", type number},
        {"longitude", type number},
        {"road_type", type text},
        {"road_lanes", Int64.Type},
        {"length_m", type number},
        {"accident_risk_score", type number},
        {"free_flow_speed_kmh", type number},
        {"corridor_label", type text}
    })
in
    ChangedTypes

// ------------------------------------------------------------------------------
// TABLE 2: dim_date
// ------------------------------------------------------------------------------
let
    Source = Csv.Document(File.Contents(ExportFolderPath & "\dim_date.csv"), [Delimiter=",", Columns=11, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangedTypes = Table.TransformColumnTypes(PromotedHeaders, {
        {"date", type date},
        {"date_key", Int64.Type},
        {"year", Int64.Type},
        {"quarter", type text},
        {"month", Int64.Type},
        {"month_name", type text},
        {"day", Int64.Type},
        {"day_of_week", Int64.Type},
        {"day_name", type text},
        {"is_weekend", Int64.Type},
        {"is_holiday", Int64.Type}
    })
in
    ChangedTypes

// ------------------------------------------------------------------------------
// TABLE 3: dim_time
// ------------------------------------------------------------------------------
let
    Source = Csv.Document(File.Contents(ExportFolderPath & "\dim_time.csv"), [Delimiter=",", Columns=6, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangedTypes = Table.TransformColumnTypes(PromotedHeaders, {
        {"hour", Int64.Type},
        {"time_key", Int64.Type},
        {"time_label", type text},
        {"period_of_day", type text},
        {"is_peak_hour", Int64.Type},
        {"peak_period_name", type text}
    })
in
    ChangedTypes

// ------------------------------------------------------------------------------
// TABLE 4: dim_event
// ------------------------------------------------------------------------------
let
    Source = Csv.Document(File.Contents(ExportFolderPath & "\dim_event.csv"), [Delimiter=",", Columns=12, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangedTypes = Table.TransformColumnTypes(PromotedHeaders, {
        {"event_id", type text},
        {"event_name", type text},
        {"event_type", type text},
        {"city", type text},
        {"date", type date},
        {"venue", type text},
        {"attendance", Int64.Type},
        {"event_intensity", type number},
        {"event_avg_congestion_pct", type number},
        {"city_baseline_congestion_pct", type number},
        {"congestion_lift_pct", type number},
        {"observations_count", Int64.Type}
    })
in
    ChangedTypes

// ------------------------------------------------------------------------------
// TABLE 5: dim_weather_category
// ------------------------------------------------------------------------------
let
    Source = Csv.Document(File.Contents(ExportFolderPath & "\dim_weather_category.csv"), [Delimiter=",", Columns=5, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangedTypes = Table.TransformColumnTypes(PromotedHeaders, {
        {"rain_category", type text},
        {"precip_min_mm", type number},
        {"precip_max_mm", type number},
        {"weather_severity", type text},
        {"advisory_level", type text}
    })
in
    ChangedTypes

// ------------------------------------------------------------------------------
// TABLE 6: fact_congestion_hourly
// ------------------------------------------------------------------------------
let
    Source = Csv.Document(File.Contents(ExportFolderPath & "\fact_congestion_hourly.csv"), [Delimiter=",", Columns=24, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangedTypes = Table.TransformColumnTypes(PromotedHeaders, {
        {"timestamp", type datetime},
        {"date", type date},
        {"date_key", Int64.Type},
        {"location_id", type text},
        {"hour", Int64.Type},
        {"day_of_week", Int64.Type},
        {"month", Int64.Type},
        {"is_weekend", Int64.Type},
        {"is_peak_hour", Int64.Type},
        {"is_holiday", Int64.Type},
        {"event_present", Int64.Type},
        {"event_name", type text},
        {"event_type", type text},
        {"event_intensity", type number},
        {"temperature_2m_c", type number},
        {"precipitation_mm", type number},
        {"is_raining", Int64.Type},
        {"relative_humidity_2m_pct", type number},
        {"wind_speed_10m_kmh", type number},
        {"observed_speed_kmh", type number},
        {"free_flow_speed_kmh", type number},
        {"congestion_percentage", type number},
        {"congestion_category", type text},
        {"speed_reduction_pct", type number}
    })
in
    ChangedTypes

// ------------------------------------------------------------------------------
// TABLE 7: model_performance_summary
// ------------------------------------------------------------------------------
let
    Source = Csv.Document(File.Contents(ExportFolderPath & "\model_performance_summary.csv"), [Delimiter=",", Columns=8, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangedTypes = Table.TransformColumnTypes(PromotedHeaders, {
        {"model_key", type text},
        {"model_name", type text},
        {"algorithm_family", type text},
        {"role", type text},
        {"mae", type number},
        {"rmse", type number},
        {"r2_score", type number},
        {"is_champion", Int64.Type}
    })
in
    ChangedTypes

// ------------------------------------------------------------------------------
// TABLE 8: model_actual_vs_predicted
// ------------------------------------------------------------------------------
let
    Source = Csv.Document(File.Contents(ExportFolderPath & "\model_actual_vs_predicted.csv"), [Delimiter=",", Columns=16, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangedTypes = Table.TransformColumnTypes(PromotedHeaders, {
        {"timestamp", type datetime},
        {"date", type date},
        {"location_id", type text},
        {"location_name", type text},
        {"city", type text},
        {"hour", Int64.Type},
        {"is_peak_hour", Int64.Type},
        {"is_weekend", Int64.Type},
        {"actual_congestion_pct", type number},
        {"pred_historical_mean", type number},
        {"pred_linear_regression", type number},
        {"pred_random_forest", type number},
        {"pred_xgboost", type number},
        {"residual_historical_mean", type number},
        {"residual_linear_regression", type number},
        {"residual_random_forest", type number},
        {"residual_xgboost", type number}
    })
in
    ChangedTypes

// ------------------------------------------------------------------------------
// TABLE 9: model_feature_importance
// ------------------------------------------------------------------------------
let
    Source = Csv.Document(File.Contents(ExportFolderPath & "\model_feature_importance.csv"), [Delimiter=",", Columns=7, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangedTypes = Table.TransformColumnTypes(PromotedHeaders, {
        {"feature_name", type text},
        {"display_name", type text},
        {"category", type text},
        {"shap_importance_pct", type number},
        {"xgboost_importance", type number},
        {"random_forest_importance", type number},
        {"ridge_coefficient", type number}
    })
in
    ChangedTypes

// ------------------------------------------------------------------------------
// TABLE 10: corridor_predictive_risk
// ------------------------------------------------------------------------------
let
    Source = Csv.Document(File.Contents(ExportFolderPath & "\corridor_predictive_risk.csv"), [Delimiter=",", Columns=15, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangedTypes = Table.TransformColumnTypes(PromotedHeaders, {
        {"location_id", type text},
        {"location_name", type text},
        {"city", type text},
        {"road_type", type text},
        {"road_lanes", Int64.Type},
        {"free_flow_speed_kmh", type number},
        {"accident_risk_score", type number},
        {"baseline_congestion_pct", type number},
        {"peak_hour_congestion_pct", type number},
        {"off_peak_congestion_pct", type number},
        {"rain_congestion_pct", type number},
        {"event_congestion_pct", type number},
        {"composite_risk_score", type number},
        {"risk_tier", type text},
        {"primary_risk_driver", type text}
    })
in
    ChangedTypes

// ------------------------------------------------------------------------------
// TABLE 11: refresh_metadata
// ------------------------------------------------------------------------------
let
    Source = Csv.Document(File.Contents(ExportFolderPath & "\refresh_metadata.csv"), [Delimiter=",", Columns=14, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangedTypes = Table.TransformColumnTypes(PromotedHeaders, {
        {"refresh_timestamp_utc", type datetimezone},
        {"refresh_date", type date},
        {"source_dataset", type text},
        {"source_dataset_records", Int64.Type},
        {"temporal_range_start", type text},
        {"temporal_range_end", type text},
        {"metropolitan_cities_count", Int64.Type},
        {"corridors_monitored_count", Int64.Type},
        {"models_evaluated_count", Int64.Type},
        {"champion_model_key", type text},
        {"champion_model_name", type text},
        {"champion_test_mae", type number},
        {"champion_test_rmse", type number},
        {"champion_test_r2", type number},
        {"pipeline_status", type text}
    })
in
    ChangedTypes
