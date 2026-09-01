CREATE TABLE IF NOT EXISTS MemoryLog (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,
    Timestamp TEXT NOT NULL,
    Module TEXT NOT NULL,
    Action TEXT NOT NULL,
    Detail TEXT,
    Success INTEGER DEFAULT 1
);
using System;
using System.Collections.Generic;
using System.Data.SQLite;
using Dapper;

namespace AIMini.Memory
{
    public class MemoryBank
    {
        private readonly string _connectionString;

        public MemoryBank(string dbPath = "ai_memory.db")
        {
            _connectionString = $"Data Source={dbPath}";
            InitializeDatabase();
        }

        private void InitializeDatabase()
        {
            using var conn = new SQLiteConnection(_connectionString);
            conn.Execute(@"
                CREATE TABLE IF NOT EXISTS MemoryLog (
                    Id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Timestamp TEXT NOT NULL,
                    Module TEXT NOT NULL,
                    Action TEXT NOT NULL,
                    Detail TEXT,
                    Success INTEGER DEFAULT 1
                )");
        }

        public void Log(string module, string action, string detail = null, bool success = true)
        {
            using var conn = new SQLiteConnection(_connectionString);
            conn.Execute(
                "INSERT INTO MemoryLog (Timestamp, Module, Action, Detail, Success) " +
                "VALUES (@Timestamp, @Module, @Action, @Detail, @Success)",
                new
                {
                    Timestamp = DateTime.UtcNow.ToString("o"),
                    Module = module,
                    Action = action,
                    Detail = detail,
                    Success = success ? 1 : 0
                });
        }

        public IEnumerable<MemoryEntry> GetRecent(int count = 10)
        {
            using var conn = new SQLiteConnection(_connectionString);
            return conn.Query<MemoryEntry>(
                "SELECT * FROM MemoryLog ORDER BY Id DESC LIMIT @Count",
                new { Count = count });
        }

        public IEnumerable<MemoryEntry> GetByModule(string module, int count = 10)
        {
            using var conn = new SQLiteConnection(_connectionString);
            return conn.Query<MemoryEntry>(
                "SELECT * FROM MemoryLog WHERE Module = @Module ORDER BY Id DESC LIMIT @Count",
                new { Module = module, Count = count });
        }

        public void Clear()
        {
            using var conn = new SQLiteConnection(_connectionString);
            conn.Execute("DELETE FROM MemoryLog");
        }
    }

    public class MemoryEntry
    {
        public int Id { get; set; }
        public string Timestamp { get; set; }
        public string Module { get; set; }
        public string Action { get; set; }
        public string Detail { get; set; }
        public int Success { get; set; }
    }
}





Що ще треба зробити:

1. Додати NuGet-пакети в проєкт


  dotnet add package Dapper
   dotnet add package System.Data.SQLite.Core

2. Створити файл MemoryBank.cs і вставити код вище

3. Використовувати в будь-якому місці Ai-mini:

  var bank = new MemoryBank();
   bank.Log("PhotoAnalyzer", "Started", "processing batch #3");



Давай я закладу ідею "Spaghetti-підходу" в код AI-mini. Тобто:

1. При запуску — читає останні події (хаос спагеті)
2. Усміхається (грайливість J-Hope)
3. Вирішує, що робити далі (резонанс)

Ось код, який це реалізує. Скинь свій поточний файл AI-mini, і я додам туди цю логіку. Або якщо хочеш — ось базова версія, яку ми потім допасуємо під твій проект:



import json
import random
from datetime import datetime

