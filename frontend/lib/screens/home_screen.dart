import 'package:flutter/material.dart';
import 'dart:async'; // Import for Timer
import 'package:http/http.dart' as http; // Import for HTTP requests
import 'dart:convert'; // Import for JSON decoding
import 'package:frontend/main.dart'; // Import showNotification
import 'package:shared_preferences/shared_preferences.dart'; // Import shared_preferences
import 'package:frontend/utils/config.dart'; // Import AppConfig

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  Timer? _notificationPollingTimer;
  int? _userId;
  String? _accessToken;
  List<dynamic> _trackedProducts = [];
  bool _isLoadingProducts = true;
  String? _productsErrorMessage;

  @override
  void initState() {
    super.initState();
    _loadUserDataAndProducts();
  }

  Future<void> _loadUserDataAndProducts() async {
    final SharedPreferences prefs = await SharedPreferences.getInstance();
    setState(() {
      _userId = prefs.getInt('user_id');
      _accessToken = prefs.getString('access_token');
    });

    if (_userId == null || _accessToken == null) {
      if (mounted) {
        Navigator.pushReplacementNamed(context, '/login');
      }
      return;
    }

    // Start polling for notifications
    _notificationPollingTimer = Timer.periodic(const Duration(seconds: 30), (timer) {
      _fetchNotifications();
    });

    // Fetch tracked products initially
    _fetchTrackedProducts();
  }

  @override
  void dispose() {
    _notificationPollingTimer?.cancel();
    super.dispose();
  }

  Future<void> _fetchNotifications() async {
    if (_userId == null || _accessToken == null) return;

    final response = await http.get(
      Uri.parse('${AppConfig.baseUrl}/notifications/$_userId'),
      headers: {
        'Authorization': 'Bearer $_accessToken',
      },
    );

    if (response.statusCode == 200) {
      List<dynamic> notificationsJson = json.decode(response.body);
      for (var notificationJson in notificationsJson) {
        showNotification(
          'Price Drop Alert!',
          notificationJson['message'],
        );
        _deleteNotification(notificationJson['id']);
      }
    } else {
      print('Failed to load notifications: ${response.statusCode}');
      if (response.statusCode == 401) {
        _logout();
      }
    }
  }

  Future<void> _deleteNotification(int notificationId) async {
    if (_accessToken == null) return;

    final response = await http.delete(
      Uri.parse('${AppConfig.baseUrl}/notifications/$notificationId'),
      headers: {
        'Authorization': 'Bearer $_accessToken',
      },
    );

    if (response.statusCode == 204) {
      print('Notification $notificationId deleted successfully.');
    } else {
      print('Failed to delete notification $notificationId: ${response.statusCode}');
      if (response.statusCode == 401) {
        _logout();
      }
    }
  }

  Future<void> _fetchTrackedProducts() async {
    setState(() {
      _isLoadingProducts = true;
      _productsErrorMessage = null;
    });

    if (_accessToken == null) {
      _productsErrorMessage = 'Authentication token not found.';
      _isLoadingProducts = false;
      return;
    }

    try {
      final response = await http.get(
        Uri.parse('${AppConfig.baseUrl}/products/my_products'),
        headers: {
          'Authorization': 'Bearer $_accessToken',
        },
      );

      if (response.statusCode == 200) {
        setState(() {
          _trackedProducts = json.decode(response.body);
          _isLoadingProducts = false;
        });
      } else if (response.statusCode == 401) {
        if (mounted) {
          _logout();
        }
      } else {
        setState(() {
          _productsErrorMessage = 'Failed to load products: ${response.statusCode}';
          _isLoadingProducts = false;
        });
      }
    } catch (e) {
      setState(() {
        _productsErrorMessage = 'An error occurred while fetching products: $e';
        _isLoadingProducts = false;
      });
    }
  }

  Future<void> _logout() async {
    final SharedPreferences prefs = await SharedPreferences.getInstance();
    await prefs.remove('user_id');
    await prefs.remove('access_token');
    _notificationPollingTimer?.cancel();
    if (mounted) {
      Navigator.pushReplacementNamed(context, '/login');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Tracked Products'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: _logout,
          ),
        ],
      ),
      body: _isLoadingProducts
          ? const Center(child: CircularProgressIndicator())
          : _productsErrorMessage != null
              ? Center(child: Text(_productsErrorMessage!))
              : _trackedProducts.isEmpty
                  ? const Center(child: Text('No products tracked yet. Add some!'))
                  : ListView.builder(
                      itemCount: _trackedProducts.length,
                      itemBuilder: (context, index) {
                        final product = _trackedProducts[index];
                        return Card(
                          margin: const EdgeInsets.all(8.0),
                          child: ListTile(
                            leading: product['image_url'] != null
                                ? Image.network(product['image_url'], width: 50, height: 50, fit: BoxFit.cover)
                                : const Icon(Icons.image_not_supported),
                            title: Text(product['name']),
                            subtitle: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text('Current Price: \$${product['price'].toStringAsFixed(2)}'),
                                if (product['target_price'] != null)
                                  Text('Target Price: \$${product['target_price'].toStringAsFixed(2)}'),
                              ],
                            ),
                            trailing: const Icon(Icons.arrow_forward_ios),
                            onTap: () {
                              Navigator.pushNamed(
                                context,
                                '/product_detail',
                                arguments: product['id'],
                              ).then((_) => _fetchTrackedProducts()); // Refresh list after returning from detail
                            },
                          ),
                        );
                      },
                    ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          Navigator.pushNamed(context, '/add_product').then((_) => _fetchTrackedProducts()); // Refresh list after adding product
        },
        child: const Icon(Icons.add),
      ),
    );
  }
}

