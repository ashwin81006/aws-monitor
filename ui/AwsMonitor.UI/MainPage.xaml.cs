using AwsMonitor.UI.ViewModels;

namespace AwsMonitor.UI;

public partial class MainPage : ContentPage
{
	private readonly MainViewModel _vm;

	public MainPage(MainViewModel vm)
	{
		InitializeComponent();
		_vm = vm;
		BindingContext = _vm;
	}

	protected override async void OnAppearing()
	{
		base.OnAppearing();
		await _vm.InitializeAsync();
	}

	private void OnIncidentTapped(object? sender, TappedEventArgs e)
	{
		if (sender is VisualElement { BindingContext: Models.AnomalyEvent ev })
		{
			_vm.SelectEvent(ev);
		}
	}
}

