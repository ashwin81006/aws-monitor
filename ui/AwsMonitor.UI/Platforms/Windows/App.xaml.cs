using Microsoft.UI.Xaml;

// To learn more about WinUI, the WinUI project structure,
// and more about our project templates, see: http://aka.ms/winui-project-info.

namespace AwsMonitor.UI.WinUI;

/// <summary>
/// Provides application-specific behavior to supplement the default Application class.
/// </summary>
public partial class App : MauiWinUIApplication
{
	/// <summary>
	/// Initializes the singleton application object.  This is the first line of authored code
	/// executed, and as such is the logical equivalent of main() or WinMain().
	/// </summary>
	public App()
	{
		this.InitializeComponent();
		UnhandledException += (sender, e) =>
		{
			var msg = $"[WinUI UnhandledException] {e.Message}\r\nException: {e.Exception}\r\nStackTrace: {e.Exception?.StackTrace}\r\n";
			try { System.IO.File.AppendAllText(@"C:\Users\Ashy\.gemini\antigravity-ide\brain\08652e65-74b6-42f4-a5e2-7b0e017dc39d\scratch\crash_log.txt", msg); } catch {}
		};
		AppDomain.CurrentDomain.UnhandledException += (sender, e) =>
		{
			var msg = $"[AppDomain UnhandledException] {e.ExceptionObject}\r\n";
			try { System.IO.File.AppendAllText(@"C:\Users\Ashy\.gemini\antigravity-ide\brain\08652e65-74b6-42f4-a5e2-7b0e017dc39d\scratch\crash_log.txt", msg); } catch {}
		};
	}

	protected override MauiApp CreateMauiApp() => MauiProgram.CreateMauiApp();
}

