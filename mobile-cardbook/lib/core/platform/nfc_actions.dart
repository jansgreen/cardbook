import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:nfc_manager/ndef_record.dart';
import 'package:nfc_manager/nfc_manager.dart';
import 'package:nfc_manager/nfc_manager_android.dart';

enum NfcWriteResult {
  written,
  unsupported,
  disabled,
  notWritable,
  tooSmall,
  failed,
}

class NfcActions {
  const NfcActions._();

  static _ResultCompleter? _activeCompleter;

  static Future<NfcAvailability> availability() async {
    if (kIsWeb ||
        (defaultTargetPlatform != TargetPlatform.android &&
            defaultTargetPlatform != TargetPlatform.iOS)) {
      return NfcAvailability.unsupported;
    }
    return NfcManager.instance.checkAvailability();
  }

  static Future<NfcWriteResult> writeUrlToTag(String url) async {
    final cleanUrl = url.trim();
    if (cleanUrl.isEmpty) return NfcWriteResult.failed;

    final currentAvailability = await availability();
    if (currentAvailability == NfcAvailability.unsupported) {
      return NfcWriteResult.unsupported;
    }
    if (currentAvailability == NfcAvailability.disabled) {
      return NfcWriteResult.disabled;
    }

    final completer = _ResultCompleter();
    _activeCompleter = completer;
    final message = _urlMessage(cleanUrl);

    await NfcManager.instance.startSession(
      pollingOptions: const {NfcPollingOption.iso14443},
      alertMessageIos: 'Acerca una etiqueta NFC para guardar tu enlace.',
      onDiscovered: (tag) async {
        try {
          final result = await _writeAndroid(tag, message);
          completer.complete(result);
          if (identical(_activeCompleter, completer)) {
            _activeCompleter = null;
          }
          await NfcManager.instance.stopSession(
            alertMessageIos: result == NfcWriteResult.written
                ? 'Enlace Cardbook guardado.'
                : null,
            errorMessageIos: result == NfcWriteResult.written
                ? null
                : 'No se pudo escribir esta etiqueta NFC.',
          );
        } catch (_) {
          completer.complete(NfcWriteResult.failed);
          if (identical(_activeCompleter, completer)) {
            _activeCompleter = null;
          }
          await NfcManager.instance.stopSession(
            errorMessageIos: 'No se pudo escribir esta etiqueta NFC.',
          );
        }
      },
    );

    return completer.future.timeout(
      const Duration(seconds: 45),
      onTimeout: () async {
        await stopSession();
        return NfcWriteResult.failed;
      },
    ).whenComplete(() {
      if (identical(_activeCompleter, completer)) {
        _activeCompleter = null;
      }
    });
  }

  static Future<void> stopSession() async {
    if (kIsWeb ||
        (defaultTargetPlatform != TargetPlatform.android &&
            defaultTargetPlatform != TargetPlatform.iOS)) {
      return;
    }
    _activeCompleter?.complete(NfcWriteResult.failed);
    _activeCompleter = null;
    await NfcManager.instance.stopSession();
  }

  static Future<NfcWriteResult> _writeAndroid(
    NfcTag tag,
    NdefMessage message,
  ) async {
    final ndef = NdefAndroid.from(tag);
    if (ndef != null) {
      if (!ndef.isWritable) return NfcWriteResult.notWritable;
      if (message.byteLength > ndef.maxSize) return NfcWriteResult.tooSmall;
      await ndef.writeNdefMessage(message);
      return NfcWriteResult.written;
    }

    final formatable = NdefFormatableAndroid.from(tag);
    if (formatable == null) return NfcWriteResult.notWritable;
    await formatable.format(message);
    return NfcWriteResult.written;
  }

  static NdefMessage _urlMessage(String url) {
    return NdefMessage(
      records: [
        NdefRecord(
          typeNameFormat: TypeNameFormat.wellKnown,
          type: Uint8List.fromList(utf8.encode('U')),
          identifier: Uint8List(0),
          payload: Uint8List.fromList([0x00, ...utf8.encode(url)]),
        ),
      ],
    );
  }
}

class _ResultCompleter {
  final _completer = Completer<NfcWriteResult>();

  Future<NfcWriteResult> get future => _completer.future;

  void complete(NfcWriteResult result) {
    if (!_completer.isCompleted) _completer.complete(result);
  }
}
