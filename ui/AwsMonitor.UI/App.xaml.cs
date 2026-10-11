using Microsoft.Extensions.DependencyInjection;
using AwsMonitor.UI.ViewModels;
using AwsMonitor.UI.Services;

namespace AwsMonitor.UI;

public partial class App : Application
{
    public App()
    {
        InitializeComponent();
    }

    protected override Window CreateWindow(IActivationState? activationState)
    {
        var mainPage = Handler?.MauiContext?.Services.GetService<MainPage>()
                       ?? IPlatformApplication.Current?.Services.GetService<MainPage>()
                       ?? new MainPage(new MainViewModel(new ApiService()));

        var window = new Window(mainPage)
        {
            Title = "AWS MONITOR — Weather Station Quality Control",
            Width = 1060,
            Height = 640,
            MinimumWidth = 800,
            MinimumHeight = 500
        };
        return window;
    }
}