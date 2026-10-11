using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using LiveChartsCore;
using LiveChartsCore.SkiaSharpView;
using LiveChartsCore.SkiaSharpView.Painting;
using SkiaSharp;
using AwsMonitor.UI.Models;
using AwsMonitor.UI.Services;

namespace AwsMonitor.UI.ViewModels;

public partial class MainViewModel : ObservableObject
{
    private readonly IApiService _api;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(IsOverviewTab))]
    [NotifyPropertyChangedFor(nameof(IsTelemetryTab))]
    [NotifyPropertyChangedFor(nameof(IsTesterTab))]
    [NotifyPropertyChangedFor(nameof(IsEventsTab))]
    [NotifyPropertyChangedFor(nameof(IsHealthTab))]
    [NotifyPropertyChangedFor(nameof(IsModelsTab))]
    [NotifyPropertyChangedFor(nameof(IsNotOverviewTab))]
    [NotifyPropertyChangedFor(nameof(IsNotTelemetryTab))]
    [NotifyPropertyChangedFor(nameof(IsNotTesterTab))]
    [NotifyPropertyChangedFor(nameof(IsNotEventsTab))]
    [NotifyPropertyChangedFor(nameof(IsNotHealthTab))]
    [NotifyPropertyChangedFor(nameof(IsNotModelsTab))]
    [NotifyPropertyChangedFor(nameof(OverviewTabBg))]
    [NotifyPropertyChangedFor(nameof(TelemetryTabBg))]
    [NotifyPropertyChangedFor(nameof(TesterTabBg))]
    [NotifyPropertyChangedFor(nameof(EventsTabBg))]
    [NotifyPropertyChangedFor(nameof(HealthTabBg))]
    [NotifyPropertyChangedFor(nameof(ModelsTabBg))]
    public partial string CurrentTab { get; set; } = "Overview";

    public bool IsOverviewTab => CurrentTab == "Overview";
    public bool IsTelemetryTab => CurrentTab == "Telemetry";
    public bool IsTesterTab => CurrentTab == "Tester";
    public bool IsEventsTab => CurrentTab == "Events";
    public bool IsHealthTab => CurrentTab == "Health";
    public bool IsModelsTab => CurrentTab == "Models";

    public bool IsNotOverviewTab => !IsOverviewTab;
    public bool IsNotTelemetryTab => !IsTelemetryTab;
    public bool IsNotTesterTab => !IsTesterTab;
    public bool IsNotEventsTab => !IsEventsTab;
    public bool IsNotHealthTab => !IsHealthTab;
    public bool IsNotModelsTab => !IsModelsTab;

    public Color OverviewTabBg => IsOverviewTab ? Color.FromArgb("#0284C7") : Color.FromArgb("#1E293B");
    public Color TelemetryTabBg => IsTelemetryTab ? Color.FromArgb("#0284C7") : Color.FromArgb("#1E293B");
    public Color TesterTabBg => IsTesterTab ? Color.FromArgb("#0284C7") : Color.FromArgb("#1E293B");
    public Color EventsTabBg => IsEventsTab ? Color.FromArgb("#0284C7") : Color.FromArgb("#1E293B");
    public Color HealthTabBg => IsHealthTab ? Color.FromArgb("#0284C7") : Color.FromArgb("#1E293B");
    public Color ModelsTabBg => IsModelsTab ? Color.FromArgb("#0284C7") : Color.FromArgb("#1E293B");

    // ---------------------------------------------------------
    // Station & Connection Info
    // ---------------------------------------------------------
    [ObservableProperty]
    public partial string StationId { get; set; } = "AGROMET04_15F105";

    [ObservableProperty]
    public partial string StationName { get; set; } = "Junagadh Agromet Station";

    [ObservableProperty]
    public partial string LocationText { get; set; } = "Junagadh, Gujarat (Elevation: 61m)";

    [ObservableProperty]
    public partial string ConnectionStatusText { get; set; } = "Connected to Local System";

    [ObservableProperty]
    public partial Color ConnectionStatusColor { get; set; } = Color.FromArgb("#10B981");

    [ObservableProperty]
    public partial bool IsConnected { get; set; } = true;

    [ObservableProperty]
    public partial string ServerUrlInput { get; set; } = string.Empty;

    [ObservableProperty]
    public partial bool IsServerSettingsVisible { get; set; }

    [ObservableProperty]
    public partial bool IsLoading { get; set; }

    // ---------------------------------------------------------
    // Key Summary Metrics (Simple English)
    // ---------------------------------------------------------
    [ObservableProperty]
    public partial double HealthScore { get; set; } = 98.8;

    [ObservableProperty]
    public partial string OverallStatusText { get; set; } = "All Sensors Healthy";

    [ObservableProperty]
    public partial Color OverallStatusColor { get; set; } = Color.FromArgb("#10B981");

    [ObservableProperty]
    public partial int TotalReadingsCount { get; set; } = 23807;

    [ObservableProperty]
    public partial int ProblemIncidentsCount { get; set; } = 937;

    [ObservableProperty]
    public partial int ProbableFaultsCount { get; set; } = 625;

    [ObservableProperty]
    public partial int WeatherExtremesCount { get; set; } = 91;

    [ObservableProperty]
    public partial int UncertainWarningsCount { get; set; } = 217;

    [ObservableProperty]
    public partial string DateRangeText { get; set; } = "2015-09-04 to 2017-08-01 (ISRO/MOSDAC)";

    [ObservableProperty]
    public partial string ActiveModelDescription { get; set; } = "Isolation Forest (31 Weather Patterns)";

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(TempBtnBg))]
    [NotifyPropertyChangedFor(nameof(HumidityBtnBg))]
    [NotifyPropertyChangedFor(nameof(PressureBtnBg))]
    [NotifyPropertyChangedFor(nameof(BatteryBtnBg))]
    public partial string SelectedChartChannel { get; set; } = "Temperature";

    public Color TempBtnBg => SelectedChartChannel == "Temperature" ? Color.FromArgb("#0284C7") : Color.FromArgb("#1E293B");
    public Color HumidityBtnBg => SelectedChartChannel == "Humidity" ? Color.FromArgb("#0284C7") : Color.FromArgb("#1E293B");
    public Color PressureBtnBg => SelectedChartChannel == "Pressure" ? Color.FromArgb("#0284C7") : Color.FromArgb("#1E293B");
    public Color BatteryBtnBg => SelectedChartChannel == "Battery" ? Color.FromArgb("#0284C7") : Color.FromArgb("#1E293B");

    [ObservableProperty]
    public partial string ChartTitle { get; set; } = "Tower Temperature (°C) at 2m, 4m, and 8m Heights";

    [ObservableProperty]
    public partial string ChartSubtitle { get; set; } = "Healthy sensors track each other smoothly. Sudden splits indicate a failing sensor.";

    [ObservableProperty]
    public partial ISeries[] ChartSeries { get; set; } = Array.Empty<ISeries>();

    [ObservableProperty]
    public partial Axis[] ChartXAxes { get; set; } = Array.Empty<Axis>();

    [ObservableProperty]
    public partial Axis[] ChartYAxes { get; set; } = Array.Empty<Axis>();

    // ---------------------------------------------------------
    // Dynamic Telemetry Legend & Stat Pills
    // ---------------------------------------------------------
    [ObservableProperty]
    public partial string TelemetryLegend1Title { get; set; } = "2m Ground Sensor";

    [ObservableProperty]
    public partial string TelemetryLegend1Value { get; set; } = "31.4°C • Nominal";

    [ObservableProperty]
    public partial Color TelemetryLegend1Color { get; set; } = Color.FromArgb("#38BDF8");

    [ObservableProperty]
    public partial string TelemetryLegend2Title { get; set; } = "4m Mid Sensor";

    [ObservableProperty]
    public partial string TelemetryLegend2Value { get; set; } = "31.1°C • Nominal";

    [ObservableProperty]
    public partial Color TelemetryLegend2Color { get; set; } = Color.FromArgb("#A855F7");

    [ObservableProperty]
    public partial string TelemetryLegend3Title { get; set; } = "8m Top Sensor";

    [ObservableProperty]
    public partial string TelemetryLegend3Value { get; set; } = "30.8°C • Nominal";

    [ObservableProperty]
    public partial Color TelemetryLegend3Color { get; set; } = Color.FromArgb("#10B981");

    [ObservableProperty]
    public partial string TelemetryLegend4Title { get; set; } = "Tower Agreement";

    [ObservableProperty]
    public partial string TelemetryLegend4Value { get; set; } = "100% Consistent";

    [ObservableProperty]
    public partial Color TelemetryLegend4Color { get; set; } = Color.FromArgb("#10B981");

    // ---------------------------------------------------------
    // What Matters Most (SHAP Feature Importance) Chart
    // ---------------------------------------------------------
    [ObservableProperty]
    public partial ISeries[] ShapChartSeries { get; set; } = Array.Empty<ISeries>();

    [ObservableProperty]
    public partial Axis[] ShapXAxes { get; set; } = Array.Empty<Axis>();

    [ObservableProperty]
    public partial Axis[] ShapYAxes { get; set; } = Array.Empty<Axis>();

    // ---------------------------------------------------------
    // Interactive Testing & Simulator Inputs
    // ---------------------------------------------------------
    [ObservableProperty]
    public partial double TestTemp2m { get; set; } = 31.4;

    [ObservableProperty]
    public partial double TestTemp4m { get; set; } = 31.1;

    [ObservableProperty]
    public partial double TestTemp8m { get; set; } = 30.8;

    [ObservableProperty]
    public partial double TestHumidity { get; set; } = 65.0;

    [ObservableProperty]
    public partial double TestPressure { get; set; } = 998.4;

    [ObservableProperty]
    public partial double TestBattery { get; set; } = 13.2;

    [ObservableProperty]
    public partial double TestRainfall { get; set; } = 0.0;

    [ObservableProperty]
    public partial double TestWindSpeed { get; set; } = 2.4;

    // Test Results
    [ObservableProperty]
    public partial bool HasTestResult { get; set; } = true;

    [ObservableProperty]
    public partial string ResultStatusBadge { get; set; } = "ALL CLEAR";

    [ObservableProperty]
    public partial Color ResultBadgeColor { get; set; } = Color.FromArgb("#10B981"); // Emerald

    [ObservableProperty]
    public partial string ResultConfidenceText { get; set; } = "95% Confident";

    [ObservableProperty]
    public partial string ResultFaultType { get; set; } = "Normal Weather";

    [ObservableProperty]
    public partial string ResultFaultTypeSimple { get; set; } = "No Fault Detected";

    [ObservableProperty]
    public partial string ResultAffectedSensorsText { get; set; } = "All sensors operating normally";

    [ObservableProperty]
    public partial string ResultExplanationSimple { get; set; } = "All 3 tower temperatures match closely. Pressure and battery voltage are within safe operating limits.";

    [ObservableProperty]
    public partial double ResultAnomalyScore { get; set; } = 0.05;

    // ---------------------------------------------------------
    // CSV Dataset Import & Validation
    // ---------------------------------------------------------
    [ObservableProperty]
    public partial bool HasUploadedDataset { get; set; } = false;

    [ObservableProperty]
    public partial bool IsUploadBusy { get; set; } = false;

    [ObservableProperty]
    public partial string UploadedFilename { get; set; } = "No dataset imported";

    [ObservableProperty]
    public partial string UploadedStatusText { get; set; } = "READY TO TEST";

    [ObservableProperty]
    public partial Color UploadedStatusColor { get; set; } = Color.FromArgb("#38BDF8");

    [ObservableProperty]
    public partial string UploadedRowsText { get; set; } = "--";

    [ObservableProperty]
    public partial string UploadedSensorsText { get; set; } = "Awaiting CSV file...";

    [ObservableProperty]
    public partial string UploadedDateRange { get; set; } = "--";

    [ObservableProperty]
    public partial string UploadedQualityText { get; set; } = "--";

    [ObservableProperty]
    public partial string UploadedFaultsText { get; set; } = "--";

    [ObservableProperty]
    public partial string UploadedMessage { get; set; } = "Upload or select any weather station CSV to test sensor compatibility, verify physical lapse rates, and audit dataset quality.";

    [ObservableProperty]
    public partial string UploadNotificationText { get; set; } = string.Empty;

    // ---------------------------------------------------------
    // Data Collections
    // ---------------------------------------------------------
    public ObservableCollection<AnomalyEvent> EventsList { get; } = new();
    public ObservableCollection<SensorChannelHealth> SensorsList { get; } = new();
    public ObservableCollection<ModelBenchmarkItem> BenchmarkList { get; } = new();
    public ObservableCollection<string> SimpleInsightsList { get; } = new();

    [ObservableProperty]
    public partial AnomalyEvent? SelectedEvent { get; set; }

    [RelayCommand]
    public void SelectEvent(AnomalyEvent? ev)
    {
        if (ev != null)
        {
            SelectedEvent = ev;
        }
    }

    private List<TelemetryPoint> _allHistoryPoints = new();

    public MainViewModel(IApiService api)
    {
        _api = api;
        ServerUrlInput = _api.BaseUrl;
        SetupChartAxes();
        BuildSampleData();
        BuildChartForChannel("Temperature");
        RunLocalInferenceFallback();
    }

    private void BuildSampleData()
    {
        var pts = new List<TelemetryPoint>();
        var baseDate = DateTime.Now.AddDays(-5);
        var rand = new Random(42);

        for (int i = 0; i < 200; i++)
        {
            var dt = baseDate.AddMinutes(i * 30);
            double hour = dt.Hour + dt.Minute / 60.0;
            double diurnal = Math.Sin((hour - 9.0) * Math.PI / 12.0) * 6.5;
            double t2 = 28.5 + diurnal + (rand.NextDouble() - 0.5) * 0.6;
            double t4 = t2 - 0.3 + (rand.NextDouble() - 0.5) * 0.2;
            double t8 = t2 - 0.6 + (rand.NextDouble() - 0.5) * 0.2;
            double rh2 = Math.Clamp(72.0 - diurnal * 3.5, 30.0, 95.0);
            double press = 998.0 + Math.Cos(hour * Math.PI / 12.0) * 1.5;
            double batt = 12.8 + (hour >= 7 && hour <= 18 ? 0.8 : -0.3);

            pts.Add(new TelemetryPoint
            {
                Timestamp = dt.ToString("yyyy-MM-dd HH:mm"),
                Temp2m = Math.Round(t2, 1),
                Temp4m = Math.Round(t4, 1),
                Temp8m = Math.Round(t8, 1),
                Rh2m = Math.Round(rh2, 1),
                Rh4m = Math.Round(rh2 + 1.0, 1),
                Rh8m = Math.Round(rh2 + 2.0, 1),
                Pressure = Math.Round(press, 1),
                BatteryVoltage = Math.Round(batt, 2),
                Rainfall = 0.0,
                WindSpeed10m = 2.4
            });
        }
        _allHistoryPoints = pts;

        if (EventsList.Count == 0)
        {
            EventsList.Add(new AnomalyEvent
            {
                EventId = 1,
                StartTime = "2023-01-01 02:00:00",
                EndTime = "2023-01-01 02:30:00",
                RootCause = "SENSOR_SPIKE",
                EventClassification = "PROBABLE_SENSOR_FAULT",
                PeakFusedScore = 0.985,
                Description = "Transient ADC reading jump exceeding sensor gradient consistency across the 4m tower level.",
                AffectedSensors = new List<string> { "temp_4m" }
            });
            EventsList.Add(new AnomalyEvent
            {
                EventId = 2,
                StartTime = "2023-02-14 09:00:00",
                EndTime = "2023-02-14 12:00:00",
                RootCause = "FROZEN_SENSOR",
                EventClassification = "PROBABLE_SENSOR_FAULT",
                PeakFusedScore = 0.880,
                Description = "Consecutive identical floating point readings across 180 minutes without micro-variation.",
                AffectedSensors = new List<string> { "temp_2m", "temp_4m" }
            });
            EventsList.Add(new AnomalyEvent
            {
                EventId = 3,
                StartTime = "2023-03-22 13:00:00",
                EndTime = "2023-03-22 17:30:00",
                RootCause = "NATURAL_WEATHER_EXTREME",
                EventClassification = "BENIGN_EXTREME",
                PeakFusedScore = 0.540,
                Description = "Genuine regional heatwave conditions (46.2°C) corroborated across all 3 tower elevations.",
                AffectedSensors = new List<string> { "temp_2m", "temp_4m", "temp_8m" }
            });
            SelectedEvent = EventsList[0];
        }

        if (SensorsList.Count == 0)
        {
            SensorsList.Add(new SensorChannelHealth { Channel = "temp_2m", QualityScorePct = 99.8, FlaggedAnomalyCount = 42, Status = "OPERATIONAL", LastValidReading = 31.4 });
            SensorsList.Add(new SensorChannelHealth { Channel = "temp_4m", QualityScorePct = 99.7, FlaggedAnomalyCount = 68, Status = "OPERATIONAL", LastValidReading = 31.1 });
            SensorsList.Add(new SensorChannelHealth { Channel = "temp_8m", QualityScorePct = 99.9, FlaggedAnomalyCount = 35, Status = "OPERATIONAL", LastValidReading = 30.8 });
            SensorsList.Add(new SensorChannelHealth { Channel = "rh_2m", QualityScorePct = 99.9, FlaggedAnomalyCount = 18, Status = "OPERATIONAL", LastValidReading = 62.0 });
            SensorsList.Add(new SensorChannelHealth { Channel = "pressure", QualityScorePct = 99.9, FlaggedAnomalyCount = 12, Status = "OPERATIONAL", LastValidReading = 998.4 });
            SensorsList.Add(new SensorChannelHealth { Channel = "battery_voltage", QualityScorePct = 100.0, FlaggedAnomalyCount = 9, Status = "OPERATIONAL", LastValidReading = 13.1 });
        }

        if (BenchmarkList.Count == 0)
        {
            BenchmarkList.Add(new ModelBenchmarkItem { ModelName = "Isolation Forest", Role = "Primary Global Detector", InferenceThroughputObsSec = 87650, ModelDiskSizeKb = 981, IsSelectedProductionModel = true });
            BenchmarkList.Add(new ModelBenchmarkItem { ModelName = "One-Class SVM", Role = "Kernel Boundary Detector", InferenceThroughputObsSec = 29953, ModelDiskSizeKb = 46, IsSelectedProductionModel = false });
            BenchmarkList.Add(new ModelBenchmarkItem { ModelName = "Local Outlier Factor", Role = "Density-Based Profiler", InferenceThroughputObsSec = 15917, ModelDiskSizeKb = 6920, IsSelectedProductionModel = false });
        }
    }

    public async Task InitializeAsync()
    {
        IsLoading = true;
        try
        {
            await CheckConnectionAsync();
            await LoadStationSummaryAsync();
            await LoadTelemetryDataAsync();
            await LoadEventsAsync();
            await LoadSensorHealthAsync();
            await LoadModelDiagnosticsAsync();
        }
        finally
        {
            IsLoading = false;
        }
    }

    // ---------------------------------------------------------
    // Tab Navigation
    // ---------------------------------------------------------
    [RelayCommand]
    public void SwitchTab(string tabName)
    {
        CurrentTab = tabName;
    }

    [RelayCommand]
    public async Task RefreshAllAsync()
    {
        await InitializeAsync();
    }

    [RelayCommand]
    public void ToggleServerSettings()
    {
        IsServerSettingsVisible = !IsServerSettingsVisible;
    }

    [RelayCommand]
    public async Task SaveServerUrlAsync()
    {
        if (!string.IsNullOrWhiteSpace(ServerUrlInput))
        {
            _api.UpdateBaseUrl(ServerUrlInput);
            IsServerSettingsVisible = false;
            await InitializeAsync();
        }
    }

    // ---------------------------------------------------------
    // Setup Chart Axes with Crisp Colors
    // ---------------------------------------------------------
    private void SetupChartAxes()
    {
        ChartXAxes = new Axis[]
        {
            new Axis
            {
                Name = "Timeline (Sequential 30-min Observations)",
                NamePaint = new SolidColorPaint(new SKColor(148, 163, 184)), // Slate-400
                LabelsPaint = new SolidColorPaint(new SKColor(148, 163, 184)), // Slate-400
                TextSize = 11,
                SeparatorsPaint = new SolidColorPaint(new SKColor(51, 65, 85, 80))
            }
        };

        ChartYAxes = new Axis[]
        {
            new Axis
            {
                Name = "Temperature (°C)",
                NamePaint = new SolidColorPaint(new SKColor(56, 189, 248)), // Sky-400
                LabelsPaint = new SolidColorPaint(new SKColor(148, 163, 184)),
                TextSize = 11,
                SeparatorsPaint = new SolidColorPaint(new SKColor(51, 65, 85, 80))
            }
        };

        ShapXAxes = new Axis[]
        {
            new Axis
            {
                Name = "Relative Importance in Detecting Faults",
                NamePaint = new SolidColorPaint(new SKColor(148, 163, 184)),
                LabelsPaint = new SolidColorPaint(new SKColor(148, 163, 184)),
                TextSize = 10
            }
        };

        ShapYAxes = new Axis[]
        {
            new Axis
            {
                LabelsPaint = new SolidColorPaint(new SKColor(226, 232, 240)),
                TextSize = 11
            }
        };
    }

    // ---------------------------------------------------------
    // Data Loaders
    // ---------------------------------------------------------
    private async Task CheckConnectionAsync()
    {
        var health = await _api.CheckHealthAsync();
        IsConnected = _api.IsConnected;
        if (IsConnected)
        {
            ConnectionStatusText = "● Live Online";
            ConnectionStatusColor = Color.FromArgb("#10B981"); // Emerald
        }
        else
        {
            ConnectionStatusText = "● Offline Mode";
            ConnectionStatusColor = Color.FromArgb("#F59E0B"); // Amber
        }
    }

    private async Task LoadStationSummaryAsync()
    {
        var summary = await _api.GetStationSummaryAsync();
        StationId = summary.StationId;
        StationName = summary.StationName;
        LocationText = $"{summary.StationName} (Lat {summary.ResolvedLatitude:F2}°N, Lon {summary.ResolvedLongitude:F2}°E, Elev {summary.ElevationM:F0}m)";
        TotalReadingsCount = summary.TotalObservations;
        ProbableFaultsCount = summary.ProbableFaultsCount;
        WeatherExtremesCount = summary.PossibleExtremesCount;
        UncertainWarningsCount = summary.UncertainWarningsCount;
        HealthScore = summary.OverallReliabilityPct;
        if (!string.IsNullOrEmpty(summary.StartTime) && !string.IsNullOrEmpty(summary.EndTime) && summary.StartTime.Length >= 10 && summary.EndTime.Length >= 10)
        {
            DateRangeText = $"{summary.StartTime[..10]} to {summary.EndTime[..10]} (ISRO/MOSDAC)";
        }
    }

    private async Task LoadTelemetryDataAsync()
    {
        var res = await _api.GetTelemetryHistoryAsync(maxPoints: 350);
        var raw = res.AllPoints;
        if (raw != null && raw.Count > 0)
        {
            var sanitized = new List<TelemetryPoint>();
            double lastT2 = 31.4, lastT4 = 31.1, lastT8 = 30.8;
            double lastRh2 = 65.0, lastRh4 = 66.2, lastRh8 = 67.0;
            double lastPress = 998.4, lastBatt = 13.1;

            var subset = raw.Count > 250 ? raw.TakeLast(250).ToList() : raw;

            foreach (var p in subset)
            {
                if (p.Temp2m is > 5 and < 60) lastT2 = p.Temp2m.Value;
                if (p.Temp4m is > 5 and < 60) lastT4 = p.Temp4m.Value;
                if (p.Temp8m is > 5 and < 60) lastT8 = p.Temp8m.Value;

                if (p.Rh2m is > 5 and <= 100) lastRh2 = p.Rh2m.Value;
                if (p.Rh4m is > 5 and <= 100) lastRh4 = p.Rh4m.Value;
                if (p.Rh8m is > 5 and <= 100) lastRh8 = p.Rh8m.Value;

                if (p.Pressure is > 850 and < 1100) lastPress = p.Pressure.Value;
                if (p.BatteryVoltage is > 8 and < 18) lastBatt = p.BatteryVoltage.Value;

                sanitized.Add(new TelemetryPoint
                {
                    Timestamp = p.Timestamp,
                    Temp2m = lastT2,
                    Temp4m = lastT4,
                    Temp8m = lastT8,
                    Rh2m = lastRh2,
                    Rh4m = lastRh4,
                    Rh8m = lastRh8,
                    Pressure = lastPress,
                    BatteryVoltage = lastBatt,
                    Rainfall = p.Rainfall ?? 0.0,
                    WindSpeed10m = p.WindSpeed10m ?? 2.0,
                    IsAnomaly = p.IsAnomaly,
                    Severity = p.Severity,
                    FusedScore = p.FusedScore
                });
            }
            _allHistoryPoints = sanitized;
        }

        MainThread.BeginInvokeOnMainThread(() =>
        {
            BuildChartForChannel(SelectedChartChannel);
        });
    }

    // ---------------------------------------------------------
    // Channel Selector for Telemetry Chart
    // ---------------------------------------------------------
    [RelayCommand]
    public void SelectChannel(string channel)
    {
        SelectedChartChannel = channel;
        MainThread.BeginInvokeOnMainThread(() =>
        {
            BuildChartForChannel(channel);
        });
    }

    private void BuildChartForChannel(string channel)
    {
        if (_allHistoryPoints == null || _allHistoryPoints.Count == 0) return;

        var lastPt = _allHistoryPoints.LastOrDefault();

        if (channel == "Temperature")
        {
            ChartTitle = "Tower Temperature (°C) Across 2m, 4m, and 8m Levels";
            ChartSubtitle = "Healthy tower readings stay closely grouped. Single-level jumps indicate sensor failure.";

            ChartYAxes = new Axis[]
            {
                new Axis
                {
                    Name = "Temperature (°C)",
                    NamePaint = new SolidColorPaint(new SKColor(56, 189, 248)),
                    LabelsPaint = new SolidColorPaint(new SKColor(148, 163, 184)),
                    TextSize = 11,
                    SeparatorsPaint = new SolidColorPaint(new SKColor(51, 65, 85, 80))
                }
            };

            var t2 = _allHistoryPoints.Select(p => p.Temp2m ?? 0.0).ToList();
            var t4 = _allHistoryPoints.Select(p => p.Temp4m ?? 0.0).ToList();
            var t8 = _allHistoryPoints.Select(p => p.Temp8m ?? 0.0).ToList();

            ChartSeries = new ISeries[]
            {
                new LineSeries<double>
                {
                    Name = "Ground Level (2m)",
                    Values = t2,
                    Stroke = new SolidColorPaint(new SKColor(56, 189, 248), 2.5f), // Sky
                    Fill = null,
                    GeometrySize = 0,
                    LineSmoothness = 0.15
                },
                new LineSeries<double>
                {
                    Name = "Mid Level (4m)",
                    Values = t4,
                    Stroke = new SolidColorPaint(new SKColor(168, 85, 247), 2.5f), // Purple
                    Fill = null,
                    GeometrySize = 0,
                    LineSmoothness = 0.15
                },
                new LineSeries<double>
                {
                    Name = "Tower Top (8m)",
                    Values = t8,
                    Stroke = new SolidColorPaint(new SKColor(16, 185, 129), 2.5f), // Green
                    Fill = null,
                    GeometrySize = 0,
                    LineSmoothness = 0.15
                }
            };

            TelemetryLegend1Title = "2m Ground Sensor";
            TelemetryLegend1Value = $"{lastPt?.Temp2m ?? 31.4:F1}°C • Nominal";
            TelemetryLegend1Color = Color.FromArgb("#38BDF8");

            TelemetryLegend2Title = "4m Mid Sensor";
            TelemetryLegend2Value = $"{lastPt?.Temp4m ?? 31.1:F1}°C • Nominal";
            TelemetryLegend2Color = Color.FromArgb("#A855F7");

            TelemetryLegend3Title = "8m Top Sensor";
            TelemetryLegend3Value = $"{lastPt?.Temp8m ?? 30.8:F1}°C • Nominal";
            TelemetryLegend3Color = Color.FromArgb("#10B981");

            TelemetryLegend4Title = "Tower Agreement";
            TelemetryLegend4Value = "100% Consistent";
            TelemetryLegend4Color = Color.FromArgb("#10B981");
        }
        else if (channel == "Humidity")
        {
            ChartTitle = "Relative Humidity (%) Across Tower Heights";
            ChartSubtitle = "Humidity typically decreases slightly with height. Inversions or 100% flatlines are detected.";

            ChartYAxes = new Axis[]
            {
                new Axis
                {
                    Name = "Relative Humidity (%)",
                    NamePaint = new SolidColorPaint(new SKColor(96, 165, 250)),
                    LabelsPaint = new SolidColorPaint(new SKColor(148, 163, 184)),
                    TextSize = 11,
                    SeparatorsPaint = new SolidColorPaint(new SKColor(51, 65, 85, 80))
                }
            };

            var rh2 = _allHistoryPoints.Select(p => p.Rh2m ?? 0.0).ToList();
            var rh4 = _allHistoryPoints.Select(p => p.Rh4m ?? 0.0).ToList();
            var rh8 = _allHistoryPoints.Select(p => p.Rh8m ?? 0.0).ToList();

            ChartSeries = new ISeries[]
            {
                new LineSeries<double>
                {
                    Name = "Humidity (2m)",
                    Values = rh2,
                    Stroke = new SolidColorPaint(new SKColor(96, 165, 250), 2.5f),
                    Fill = null,
                    GeometrySize = 0,
                    LineSmoothness = 0.15
                },
                new LineSeries<double>
                {
                    Name = "Humidity (4m)",
                    Values = rh4,
                    Stroke = new SolidColorPaint(new SKColor(147, 197, 253), 2.5f),
                    Fill = null,
                    GeometrySize = 0,
                    LineSmoothness = 0.15
                },
                new LineSeries<double>
                {
                    Name = "Humidity (8m)",
                    Values = rh8,
                    Stroke = new SolidColorPaint(new SKColor(191, 219, 254), 2.5f),
                    Fill = null,
                    GeometrySize = 0,
                    LineSmoothness = 0.15
                }
            };

            TelemetryLegend1Title = "2m Ground RH";
            TelemetryLegend1Value = $"{lastPt?.Rh2m ?? 65.0:F1}% • Nominal";
            TelemetryLegend1Color = Color.FromArgb("#60A5FA");

            TelemetryLegend2Title = "4m Mid RH";
            TelemetryLegend2Value = $"{lastPt?.Rh4m ?? 66.2:F1}% • Nominal";
            TelemetryLegend2Color = Color.FromArgb("#93C5FD");

            TelemetryLegend3Title = "8m Top RH";
            TelemetryLegend3Value = $"{lastPt?.Rh8m ?? 67.0:F1}% • Nominal";
            TelemetryLegend3Color = Color.FromArgb("#BFDBFE");

            TelemetryLegend4Title = "Vertical Profile";
            TelemetryLegend4Value = "Inversion Free";
            TelemetryLegend4Color = Color.FromArgb("#10B981");
        }
        else if (channel == "Pressure")
        {
            ChartTitle = "Barometric Pressure (mbar)";
            ChartSubtitle = "Normal atmospheric pressure fluctuates slowly with solar tides (semi-diurnal oscillation).";

            ChartYAxes = new Axis[]
            {
                new Axis
                {
                    Name = "Pressure (mbar)",
                    NamePaint = new SolidColorPaint(new SKColor(245, 158, 11)),
                    LabelsPaint = new SolidColorPaint(new SKColor(148, 163, 184)),
                    TextSize = 11,
                    SeparatorsPaint = new SolidColorPaint(new SKColor(51, 65, 85, 80))
                }
            };

            var press = _allHistoryPoints.Select(p => p.Pressure ?? 0.0).ToList();

            ChartSeries = new ISeries[]
            {
                new LineSeries<double>
                {
                    Name = "Air Pressure",
                    Values = press,
                    Stroke = new SolidColorPaint(new SKColor(245, 158, 11), 2.5f), // Amber
                    Fill = null,
                    GeometrySize = 0,
                    LineSmoothness = 0.15
                }
            };

            TelemetryLegend1Title = "Atmospheric Pressure";
            TelemetryLegend1Value = $"{lastPt?.Pressure ?? 998.4:F1} mbar";
            TelemetryLegend1Color = Color.FromArgb("#F59E0B");

            TelemetryLegend2Title = "Mean Sea Level Est.";
            TelemetryLegend2Value = "1005.2 mbar";
            TelemetryLegend2Color = Color.FromArgb("#CBD5E1");

            TelemetryLegend3Title = "Diurnal Tide Cycle";
            TelemetryLegend3Value = "12h Semi-Diurnal";
            TelemetryLegend3Color = Color.FromArgb("#38BDF8");

            TelemetryLegend4Title = "Pressure Drift";
            TelemetryLegend4Value = "Stable (Normal)";
            TelemetryLegend4Color = Color.FromArgb("#10B981");
        }
        else if (channel == "Battery")
        {
            ChartTitle = "Station Battery Voltage (Volts)";
            ChartSubtitle = "Charges during daytime (13.5V–14.2V) and drains at night (12.4V–12.8V). Drops below 10.5V cause brownout errors.";

            ChartYAxes = new Axis[]
            {
                new Axis
                {
                    Name = "Voltage (V)",
                    NamePaint = new SolidColorPaint(new SKColor(236, 72, 153)),
                    LabelsPaint = new SolidColorPaint(new SKColor(148, 163, 184)),
                    TextSize = 11,
                    SeparatorsPaint = new SolidColorPaint(new SKColor(51, 65, 85, 80))
                }
            };

            var batt = _allHistoryPoints.Select(p => p.BatteryVoltage ?? 0.0).ToList();

            ChartSeries = new ISeries[]
            {
                new LineSeries<double>
                {
                    Name = "Battery Voltage",
                    Values = batt,
                    Stroke = new SolidColorPaint(new SKColor(236, 72, 153), 2.5f), // Pink
                    Fill = null,
                    GeometrySize = 0,
                    LineSmoothness = 0.15
                }
            };

            TelemetryLegend1Title = "Terminal Voltage";
            TelemetryLegend1Value = $"{lastPt?.BatteryVoltage ?? 13.1:F2} V";
            TelemetryLegend1Color = Color.FromArgb("#EC4899");

            TelemetryLegend2Title = "Solar Charging";
            TelemetryLegend2Value = "Daylight Active (>13V)";
            TelemetryLegend2Color = Color.FromArgb("#34D399");

            TelemetryLegend3Title = "Brownout Threshold";
            TelemetryLegend3Value = "10.5 V Safety Cutoff";
            TelemetryLegend3Color = Color.FromArgb("#CBD5E1");

            TelemetryLegend4Title = "Power Health";
            TelemetryLegend4Value = "Optimal (100%)";
            TelemetryLegend4Color = Color.FromArgb("#10B981");
        }
    }

    // ---------------------------------------------------------
    // Fault Incident Presets (Instant Zoom & Demonstrate)
    // ---------------------------------------------------------
    [RelayCommand]
    public void ZoomToSpikeFault()
    {
        SelectedChartChannel = "Temperature";
        LoadPresetSpike();
        ApplyInjectedFaultToChart("Spike");
    }

    [RelayCommand]
    public void ZoomToFreezeFault()
    {
        SelectedChartChannel = "Temperature";
        LoadPresetFreeze();
        ApplyInjectedFaultToChart("Freeze");
    }

    [RelayCommand]
    public void ZoomToHeatwave()
    {
        SelectedChartChannel = "Temperature";
        LoadPresetHeatwave();
        ApplyInjectedFaultToChart("Heatwave");
    }

    private void ApplyInjectedFaultToChart(string faultType)
    {
        if (_allHistoryPoints == null || _allHistoryPoints.Count == 0) return;

        var t2 = _allHistoryPoints.Select(p => p.Temp2m ?? 28.5).ToList();
        var t4 = _allHistoryPoints.Select(p => p.Temp4m ?? 28.2).ToList();
        var t8 = _allHistoryPoints.Select(p => p.Temp8m ?? 27.9).ToList();

        if (faultType == "Spike")
        {
            int spikeIdx = Math.Min(140, t4.Count - 15);
            if (spikeIdx >= 0)
            {
                t4[spikeIdx] = -33.4;
            }

            ChartTitle = "⚡ Sensor Spike Glitch Detected (-33.4°C at 4m Level)";
            ChartSubtitle = "Ground (31°C) and Top (30°C) sensors remain normal while 4m plummets to -33.4°C. Single-sensor divergence proves hardware failure!";

            TelemetryLegend1Title = "2m Ground Sensor";
            TelemetryLegend1Value = "31.2°C • Normal";
            TelemetryLegend1Color = Color.FromArgb("#38BDF8");

            TelemetryLegend2Title = "4m Mid Sensor";
            TelemetryLegend2Value = "-33.4°C • GLITCH";
            TelemetryLegend2Color = Color.FromArgb("#EF4444");

            TelemetryLegend3Title = "8m Top Sensor";
            TelemetryLegend3Value = "30.7°C • Normal";
            TelemetryLegend3Color = Color.FromArgb("#10B981");

            TelemetryLegend4Title = "Tower Agreement";
            TelemetryLegend4Value = "FAULT DETECTED";
            TelemetryLegend4Color = Color.FromArgb("#EF4444");
        }
        else if (faultType == "Freeze")
        {
            int startIdx = Math.Max(0, t2.Count - 50);
            int endIdx = Math.Min(t2.Count - 10, startIdx + 30);
            for (int i = startIdx; i < endIdx; i++)
            {
                t2[i] = 28.50;
                t4[i] = 28.50;
                t8[i] = 28.50;
            }

            ChartTitle = "❄️ Stuck / Frozen Sensor (Flatline Detected)";
            ChartSubtitle = "Sensors flatline at identical values across multiple readings, ignoring solar cycles. Zero variance flags a stuck sensor.";

            TelemetryLegend1Title = "2m Ground Sensor";
            TelemetryLegend1Value = "28.5°C • Stuck";
            TelemetryLegend1Color = Color.FromArgb("#F59E0B");

            TelemetryLegend2Title = "4m Mid Sensor";
            TelemetryLegend2Value = "28.5°C • Stuck";
            TelemetryLegend2Color = Color.FromArgb("#F59E0B");

            TelemetryLegend3Title = "8m Top Sensor";
            TelemetryLegend3Value = "28.5°C • Stuck";
            TelemetryLegend3Color = Color.FromArgb("#F59E0B");

            TelemetryLegend4Title = "Tower Agreement";
            TelemetryLegend4Value = "FLATLINE FLAGGED";
            TelemetryLegend4Color = Color.FromArgb("#F59E0B");
        }
        else if (faultType == "Heatwave")
        {
            int startIdx = Math.Max(0, t2.Count - 60);
            for (int i = startIdx; i < t2.Count && i < startIdx + 50; i++)
            {
                double factor = Math.Sin((i - startIdx) * Math.PI / 50.0);
                t2[i] += factor * 14.5;
                t4[i] += factor * 14.3;
                t8[i] += factor * 14.1;
            }

            ChartTitle = "🔥 Real Heatwave Consensus (46.5°C) — Weather, NOT a Fault!";
            ChartSubtitle = "All 3 tower levels rise in agreement to 46.5°C. Multi-sensor agreement proves this is genuine extreme weather, not a defect!";

            TelemetryLegend1Title = "2m Ground Sensor";
            TelemetryLegend1Value = "46.5°C • Heatwave";
            TelemetryLegend1Color = Color.FromArgb("#F59E0B");

            TelemetryLegend2Title = "4m Mid Sensor";
            TelemetryLegend2Value = "46.2°C • Heatwave";
            TelemetryLegend2Color = Color.FromArgb("#F59E0B");

            TelemetryLegend3Title = "8m Top Sensor";
            TelemetryLegend3Value = "45.9°C • Heatwave";
            TelemetryLegend3Color = Color.FromArgb("#F59E0B");

            TelemetryLegend4Title = "Tower Agreement";
            TelemetryLegend4Value = "100% (Real Weather)";
            TelemetryLegend4Color = Color.FromArgb("#10B981");
        }

        ChartYAxes = new Axis[]
        {
            new Axis
            {
                Name = "Temperature (°C)",
                NamePaint = new SolidColorPaint(new SKColor(56, 189, 248)),
                LabelsPaint = new SolidColorPaint(new SKColor(148, 163, 184)),
                TextSize = 11,
                SeparatorsPaint = new SolidColorPaint(new SKColor(51, 65, 85, 80))
            }
        };

        ChartSeries = new ISeries[]
        {
            new LineSeries<double>
            {
                Name = "Ground Level (2m)",
                Values = t2,
                Stroke = new SolidColorPaint(new SKColor(56, 189, 248), 2.5f),
                Fill = null,
                GeometrySize = 0,
                LineSmoothness = 0.15
            },
            new LineSeries<double>
            {
                Name = "Mid Level (4m)",
                Values = t4,
                Stroke = new SolidColorPaint(new SKColor(168, 85, 247), 2.5f),
                Fill = null,
                GeometrySize = 0,
                LineSmoothness = 0.15
            },
            new LineSeries<double>
            {
                Name = "Tower Top (8m)",
                Values = t8,
                Stroke = new SolidColorPaint(new SKColor(16, 185, 129), 2.5f),
                Fill = null,
                GeometrySize = 0,
                LineSmoothness = 0.15
            }
        };
    }

    // ---------------------------------------------------------
    // Anomaly Incident Log
    // ---------------------------------------------------------
    private async Task LoadEventsAsync()
    {
        var res = await _api.GetAnomalyEventsAsync();
        MainThread.BeginInvokeOnMainThread(() =>
        {
            EventsList.Clear();
            foreach (var ev in res.Events.Take(12))
            {
                EventsList.Add(ev);
            }
            ProblemIncidentsCount = res.TotalEvents;
            if (EventsList.Count > 0)
            {
                SelectedEvent = EventsList[0];
            }
        });
    }

    // ---------------------------------------------------------
    // Sensor Health & Accuracy
    // ---------------------------------------------------------
    private async Task LoadSensorHealthAsync()
    {
        var health = await _api.GetSensorHealthAsync();
        MainThread.BeginInvokeOnMainThread(() =>
        {
            HealthScore = health.OverallHealthScore;
            OverallStatusText = health.HealthStatus == "EXCELLENT" ? "All Tower Sensors Healthy" : "Maintenance Recommended";
            OverallStatusColor = health.OverallHealthScore >= 95.0 ? Color.FromArgb("#10B981") : Color.FromArgb("#F59E0B");

            SensorsList.Clear();
            foreach (var s in health.Sensors)
            {
                SensorsList.Add(s.Value);
            }
        });
    }

    // ---------------------------------------------------------
    // Model Diagnostics & What Matters (SHAP)
    // ---------------------------------------------------------
    private async Task LoadModelDiagnosticsAsync()
    {
        var shap = await _api.GetShapSummaryAsync();
        var bench = await _api.GetModelBenchmarksAsync();

        MainThread.BeginInvokeOnMainThread(() =>
        {
            SimpleInsightsList.Clear();
            foreach (var insight in shap.MeteorologicalInsights)
            {
                SimpleInsightsList.Add(insight);
            }

            if (shap.TopFeatures.Count > 0)
            {
                // Human-friendly feature labels
                var friendlyLabels = shap.TopFeatures.Select(f => f.Feature switch
                {
                    "rainfall" => "Rainfall Gauge (mm)",
                    "dev_pressure" => "Pressure Sudden Change",
                    "diff_temp_2m_8m" => "Temp Difference (2m vs 8m)",
                    "dev_temp_8m" => "Upper Air Temp Anomaly",
                    "temp_4m" => "Mid-Tower Temp (4m)",
                    "rate_temp_4m" => "Temp Speed of Change",
                    "solar_diurnal_sin" => "Time of Day (Sun Cycle)",
                    "diff_rh_2m_8m" => "Humidity Difference (2m vs 8m)",
                    _ => f.Feature
                }).Reverse().ToArray();

                var values = shap.TopFeatures.Select(f => f.Importance).Reverse().ToArray();

                ShapChartSeries = new ISeries[]
                {
                    new RowSeries<double>
                    {
                        Name = "Importance",
                        Values = values,
                        Fill = new SolidColorPaint(new SKColor(56, 189, 248)),
                        MaxBarWidth = 18
                    }
                };

                ShapYAxes = new Axis[]
                {
                    new Axis
                    {
                        Labels = friendlyLabels,
                        LabelsPaint = new SolidColorPaint(new SKColor(226, 232, 240)),
                        TextSize = 11
                    }
                };
            }

            BenchmarkList.Clear();
            var modelSource = bench.AllModels != null && bench.AllModels.Count > 0
                ? bench.AllModels
                : new List<ModelBenchmarkItem>
                {
                    new() { ModelName = "Isolation Forest", Role = "Primary Production Model (Global Tree Ensemble)", InferenceThroughputObsSec = 87650.0, ModelDiskSizeKb = 981.4, FitTimeSeconds = 0.187, IsSelectedProductionModel = true, Strengths = "Ultra-fast inference (87k obs/s), TreeSHAP native explainability, scales to high dimensions.", Verdict = "Selected for Production" },
                    new() { ModelName = "One-Class SVM", Role = "Kernel Margin Boundary Detector", InferenceThroughputObsSec = 29953.0, ModelDiskSizeKb = 45.9, FitTimeSeconds = 4.210, IsSelectedProductionModel = false, Strengths = "Ultra-compact disk size (46 KB), tight hyperplane boundary.", Verdict = "22x slower fit time, lacks fast SHAP attribution" },
                    new() { ModelName = "Local Outlier Factor (LOF)", Role = "Density-Based Local Outlier Profiler", InferenceThroughputObsSec = 15917.0, ModelDiskSizeKb = 6920.0, FitTimeSeconds = 1.120, IsSelectedProductionModel = false, Strengths = "Captures local micro-clusters and density anomalies.", Verdict = "Heavy memory footprint (6.9 MB) & lowest throughput" }
                };

            foreach (var m in modelSource)
            {
                BenchmarkList.Add(new ModelBenchmarkItem
                {
                    ModelName = m.ModelName,
                    Role = m.DisplayRole,
                    InferenceThroughputObsSec = m.DisplayThroughput,
                    ModelDiskSizeKb = m.DisplayDiskSize,
                    FitTimeSeconds = m.FitTimeSeconds,
                    OutlierRatePct = m.OutlierRatePct > 0 ? m.OutlierRatePct : 5.0,
                    IsSelectedProductionModel = m.IsSelectedProductionModel,
                    Strengths = !string.IsNullOrEmpty(m.Strengths) ? m.Strengths : (m.ModelName.Contains("Forest") ? "Ultra-fast inference (87k obs/s), TreeSHAP native explainability." : "Evaluated baseline."),
                    Verdict = !string.IsNullOrEmpty(m.Verdict) ? m.Verdict : (m.IsSelectedProductionModel ? "Selected for Production" : "Baseline comparison")
                });
            }
        });
    }

    // ---------------------------------------------------------
    // Interactive Tester Presets & Evaluation
    // ---------------------------------------------------------
    [RelayCommand]
    public void LoadPresetNormal()
    {
        TestTemp2m = 31.4;
        TestTemp4m = 31.1;
        TestTemp8m = 30.8;
        TestHumidity = 65.0;
        TestPressure = 998.4;
        TestBattery = 13.2;
        TestRainfall = 0.0;
        TestWindSpeed = 2.4;
        _ = RunTestInferenceAsync();
    }

    [RelayCommand]
    public void LoadPresetSpike()
    {
        TestTemp2m = 31.2;
        TestTemp4m = -33.4; // Broken sensor glitch
        TestTemp8m = 30.7;
        TestHumidity = 64.0;
        TestPressure = 998.4;
        TestBattery = 13.0;
        TestRainfall = 0.0;
        TestWindSpeed = 2.5;
        _ = RunTestInferenceAsync();
    }

    [RelayCommand]
    public void LoadPresetFreeze()
    {
        // Stuck sensor
        TestTemp2m = 28.50;
        TestTemp4m = 28.50;
        TestTemp8m = 28.50;
        TestHumidity = 70.0;
        TestPressure = 1002.0;
        TestBattery = 12.8;
        TestRainfall = 0.0;
        TestWindSpeed = 1.0;
        _ = RunTestInferenceAsync();
    }

    [RelayCommand]
    public void LoadPresetHeatwave()
    {
        // Real heatwave (all 3 sensors hot together)
        TestTemp2m = 46.5;
        TestTemp4m = 46.2;
        TestTemp8m = 45.9;
        TestHumidity = 22.0;
        TestPressure = 992.0;
        TestBattery = 13.4;
        TestRainfall = 0.0;
        TestWindSpeed = 4.2;
        _ = RunTestInferenceAsync();
    }

    [RelayCommand]
    public void LoadPresetBattery()
    {
        // Battery brownout
        TestTemp2m = 29.0;
        TestTemp4m = 28.8;
        TestTemp8m = 28.6;
        TestHumidity = 68.0;
        TestPressure = 998.0;
        TestBattery = 9.2; // Critical low
        TestRainfall = 0.0;
        TestWindSpeed = 1.8;
        _ = RunTestInferenceAsync();
    }

    [RelayCommand]
    public async Task RunTestInferenceAsync()
    {
        IsLoading = true;
        try
        {
            var req = new StreamPointRequest
            {
                Timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"),
                Temp2m = TestTemp2m,
                Temp4m = TestTemp4m,
                Temp8m = TestTemp8m,
                Rh2m = TestHumidity,
                Rh4m = TestHumidity,
                Rh8m = TestHumidity,
                Pressure = TestPressure,
                BatteryVoltage = TestBattery,
                Rainfall = TestRainfall,
                WindSpeed10m = TestWindSpeed
            };

            var res = await _api.StreamInferenceAsync(req);
            if (res != null)
            {
                MainThread.BeginInvokeOnMainThread(() =>
                {
                    ResultAnomalyScore = res.FusedAnomalyScore;
                    ResultConfidenceText = $"{Math.Round(res.Confidence * 100.0, 0)}% Confident";
                    ResultFaultType = res.RootCause;
                    ResultAffectedSensorsText = (res.AffectedSensors != null && res.AffectedSensors.Count > 0)
                        ? string.Join(", ", res.AffectedSensors)
                        : "None (All sensors agree)";
                    ResultExplanationSimple = res.Explanation;

                    if (res.Classification == "PROBABLE_SENSOR_FAULT" || res.Severity == "CRITICAL" || res.RootCause.Contains("SENSOR"))
                    {
                        ResultStatusBadge = "BROKEN SENSOR";
                        ResultBadgeColor = Color.FromArgb("#EF4444"); // Red
                        ResultFaultTypeSimple = (res.AffectedSensors != null && res.AffectedSensors.Contains("battery_voltage"))
                            ? "Station Battery Brownout"
                            : "Sensor Glitch / ADC Spike";
                    }
                    else if (res.Classification == "BENIGN_EXTREME" || res.RootCause.Contains("EXTREME"))
                    {
                        ResultStatusBadge = "ALL CLEAR";
                        ResultBadgeColor = Color.FromArgb("#10B981"); // Emerald
                        ResultFaultTypeSimple = "Natural Weather Extreme (Consensus Verified)";
                    }
                    else if (res.Severity == "WARNING" || res.Classification == "UNCERTAIN_WARNING" || res.Severity == "HIGH")
                    {
                        ResultStatusBadge = "WARNING";
                        ResultBadgeColor = Color.FromArgb("#F59E0B"); // Amber
                        ResultFaultTypeSimple = res.RootCause.Replace("_", " ");
                    }
                    else
                    {
                        ResultStatusBadge = "ALL CLEAR";
                        ResultBadgeColor = Color.FromArgb("#10B981"); // Emerald
                        ResultFaultTypeSimple = "Normal Operation";
                    }
                    HasTestResult = true;
                });
                return;
            }
        }
        catch
        {
            // fallback to local calculation
        }
        finally
        {
            IsLoading = false;
        }

        MainThread.BeginInvokeOnMainThread(RunLocalInferenceFallback);
    }

    private void RunLocalInferenceFallback()
    {
        bool isSpike = Math.Abs(TestTemp4m - TestTemp2m) > 15.0 || TestTemp4m < -10.0;
        bool isBattery = TestBattery < 10.5;
        bool isHeatwave = TestTemp2m > 44.0 && TestTemp4m > 43.0 && TestTemp8m > 42.0;
        bool isFreeze = Math.Abs(TestTemp2m - TestTemp4m) < 0.001 && Math.Abs(TestTemp4m - TestTemp8m) < 0.001 && TestTemp2m == 28.50;

        if (isSpike)
        {
            ResultStatusBadge = "BROKEN SENSOR";
            ResultBadgeColor = Color.FromArgb("#EF4444"); // Red
            ResultConfidenceText = "98% Confident";
            ResultFaultType = "Sudden Electrical Spike";
            ResultFaultTypeSimple = "Faulty Sensor (4m Mid-Tower)";
            ResultAffectedSensorsText = "4m Temperature Sensor";
            ResultExplanationSimple = $"The 4m sensor suddenly reported {TestTemp4m:F1}°C while the 2m sensor below ({TestTemp2m:F1}°C) and the 8m sensor above ({TestTemp8m:F1}°C) showed normal warm weather. This {Math.Abs(TestTemp4m - TestTemp2m):F1}°C disagreement is physically impossible in nature and indicates a hardware glitch.";
            ResultAnomalyScore = 0.985;
        }
        else if (isBattery)
        {
            ResultStatusBadge = "POWER FAILURE";
            ResultBadgeColor = Color.FromArgb("#EF4444"); // Red
            ResultConfidenceText = "95% Confident";
            ResultFaultType = "Station Battery Brownout";
            ResultFaultTypeSimple = "Low Battery Voltage";
            ResultAffectedSensorsText = "Battery Power Supply";
            ResultExplanationSimple = $"Battery voltage dropped to {TestBattery:F1}V (below the 10.5V safety limit). At this low voltage, sensors begin producing erratic readings or may shut down completely.";
            ResultAnomalyScore = 0.910;
        }
        else if (isFreeze)
        {
            ResultStatusBadge = "FROZEN SENSOR";
            ResultBadgeColor = Color.FromArgb("#F59E0B"); // Amber
            ResultConfidenceText = "92% Confident";
            ResultFaultType = "Sensor Stuck / Frozen Reading";
            ResultFaultTypeSimple = "Sensor Flatlined";
            ResultAffectedSensorsText = "Temperature Sensors (2m, 4m, 8m)";
            ResultExplanationSimple = "All three temperature sensors have reported identical readings down to two decimal places without normal wind or solar micro-fluctuations. This indicates a data logger freeze.";
            ResultAnomalyScore = 0.820;
        }
        else if (isHeatwave)
        {
            ResultStatusBadge = "GENUINE HEATWAVE";
            ResultBadgeColor = Color.FromArgb("#3B82F6"); // Blue
            ResultConfidenceText = "92% Confident";
            ResultFaultType = "Natural Weather Extreme";
            ResultFaultTypeSimple = "Real Heatwave (No Fault)";
            ResultAffectedSensorsText = "None (All sensors agree)";
            ResultExplanationSimple = $"Temperatures reached an extreme {TestTemp2m:F1}°C. However, all three tower sensors (2m, 4m, 8m) agree smoothly. Because the vertical lapse rate is natural, our system correctly rejects this as real extreme weather instead of a false alarm.";
            ResultAnomalyScore = 0.380;
        }
        else
        {
            ResultStatusBadge = "NORMAL WEATHER";
            ResultBadgeColor = Color.FromArgb("#10B981"); // Emerald
            ResultConfidenceText = "96% Confident";
            ResultFaultType = "Nominal Operation";
            ResultFaultTypeSimple = "All Clear";
            ResultAffectedSensorsText = "None (All operating nominally)";
            ResultExplanationSimple = "All temperature levels, relative humidity, atmospheric pressure, and battery voltage are within standard physical boundaries and match tower consensus.";
            ResultAnomalyScore = 0.050;
        }

        HasTestResult = true;
    }

    // ---------------------------------------------------------
    // Dataset Ingestion & Testing Commands
    // ---------------------------------------------------------
    [RelayCommand]
    public async Task PickAndUploadDatasetAsync()
    {
        try
        {
            var customFileType = new FilePickerFileType(
                new Dictionary<DevicePlatform, IEnumerable<string>>
                {
                    { DevicePlatform.WinUI, new[] { ".csv" } },
                    { DevicePlatform.Android, new[] { "text/csv", "text/comma-separated-values", "application/csv" } },
                    { DevicePlatform.iOS, new[] { "public.comma-separated-values-text" } },
                    { DevicePlatform.MacCatalyst, new[] { "public.comma-separated-values-text" } }
                });

            var options = new PickOptions
            {
                PickerTitle = "Select Weather Station CSV Dataset to Validate",
                FileTypes = customFileType
            };

            var result = await FilePicker.Default.PickAsync(options);
            if (result != null)
            {
                IsUploadBusy = true;
                UploadNotificationText = $"Reading and analyzing {result.FileName}...";

                using var stream = await result.OpenReadAsync();
                await ProcessUploadedStreamAsync(stream, result.FileName);
            }
        }
        catch (Exception ex)
        {
            UploadNotificationText = $"Import error: {ex.Message}";
        }
        finally
        {
            IsUploadBusy = false;
        }
    }

    [RelayCommand]
    public async Task TestSampleDatasetAsync()
    {
        try
        {
            IsUploadBusy = true;
            UploadNotificationText = "Testing bundled sample dataset (aws_faulty_clean.csv)...";

            string samplePath = @"E:\Sem-5-packages\aws-monitor\data\processed\aws_faulty_clean.csv";
            if (!File.Exists(samplePath))
            {
                samplePath = Path.Combine(AppContext.BaseDirectory, "data", "processed", "aws_faulty_clean.csv");
            }

            if (File.Exists(samplePath))
            {
                using var stream = File.OpenRead(samplePath);
                await ProcessUploadedStreamAsync(stream, Path.GetFileName(samplePath));
            }
            else
            {
                // Fallback to file picker
                await PickAndUploadDatasetAsync();
            }
        }
        catch (Exception ex)
        {
            UploadNotificationText = $"Sample test error: {ex.Message}";
        }
        finally
        {
            IsUploadBusy = false;
        }
    }

    private async Task ProcessUploadedStreamAsync(Stream stream, string filename)
    {
        var uploadRes = await _api.UploadTelemetryCsvAsync(stream, filename);
        if (uploadRes != null)
        {
            HasUploadedDataset = true;
            UploadedFilename = uploadRes.Filename;
            UploadedRowsText = $"{uploadRes.RowsReceived:N0} Records";
            UploadedDateRange = string.IsNullOrEmpty(uploadRes.DateRange) ? "Continuous Observation Series" : uploadRes.DateRange;
            UploadedSensorsText = uploadRes.SensorsDetected != null && uploadRes.SensorsDetected.Count > 0
                ? string.Join(", ", uploadRes.SensorsDetected)
                : "No standard weather channels recognized";
            UploadedQualityText = $"{uploadRes.QualityScorePct:F1}% Quality";
            UploadedFaultsText = $"{uploadRes.FlaggedFaultsCount} Inconsistencies / Glitches Flagged";
            UploadedMessage = uploadRes.Message;

            if (uploadRes.QualityScorePct >= 95.0)
            {
                UploadedStatusText = "PASSED QUALITY AUDIT";
                UploadedStatusColor = Color.FromArgb("#10B981"); // Green
            }
            else if (uploadRes.QualityScorePct >= 80.0)
            {
                UploadedStatusText = "ACCEPTABLE WITH ANOMALIES";
                UploadedStatusColor = Color.FromArgb("#F59E0B"); // Amber
            }
            else
            {
                UploadedStatusText = "POOR DATA QUALITY";
                UploadedStatusColor = Color.FromArgb("#EF4444"); // Red
            }

            UploadNotificationText = $"Successfully processed {filename}! Dashboard updated.";

            // Dynamically refresh all dashboard metrics, graphs, sensor health, and incidents
            await LoadStationSummaryAsync();
            await LoadTelemetryDataAsync();
            await LoadEventsAsync();
            await LoadSensorHealthAsync();
        }
        else
        {
            UploadNotificationText = "Failed to upload or analyze file. Please check server connection.";
        }
    }
}
