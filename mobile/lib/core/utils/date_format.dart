import 'package:intl/intl.dart';

String formatFrenchDateTime(DateTime utcDate) {
  final local = utcDate.toLocal();
  final formatter = DateFormat("EEE d MMM yyyy HH:mm", 'fr_FR');
  return formatter.format(local);
}
