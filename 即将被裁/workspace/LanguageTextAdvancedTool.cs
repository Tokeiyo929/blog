using UnityEngine;
using UnityEditor;
using UnityEngine.UI;
using UnityEditor.SceneManagement;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System;
using System.Linq;

namespace EvonyExtension.Editor
{
    [System.Serializable]
    public class PrefabKeyData
    {
        public string prefabName;
        public List<string> requiredKeys = new List<string>();
        public string lastModified;
        public int keyCount;
    }

    [System.Serializable]
    public class AllPrefabsKeyConfig
    {
        public List<PrefabKeyData> prefabs = new List<PrefabKeyData>();
        public int totalPrefabs = 0;
        public int totalKeys = 0;
        public string lastModified = "";
        public string description = "所有预制体的多语言Key统一配置文件";
    }

    public class LanguageTextAdvancedTool : EditorWindow
    {
        [MenuItem("Tools/LanguageText/高级工具 - Key比对与管理")]
        private static void ShowWindow()
        {
            LanguageTextAdvancedTool window = GetWindow<LanguageTextAdvancedTool>("多语言高级工具");
            window.minSize = new Vector2(800, 600);
            window.Show();
        }

        // 比对功能相关变量
        private string keyListInput = "";
        private string jsonFilePath = "Assets/PrefabKeyConfigs/AllPrefabsKeys.json";
        private string currentPrefabName = "";
        private List<string> missingKeys = new List<string>();
        private List<string> extraKeys = new List<string>();

        // 标签页控制变量
        private int selectedTab = 0;

        // 当前配置文件中的所有预制体数据
        private AllPrefabsKeyConfig allPrefabsConfig = new AllPrefabsKeyConfig();

        // 用于显示预制体中提取的Key
        private List<string> extractedKeys = new List<string>();
        private Vector2 extractedKeysScrollPosition;
        private int extractedKeyCount = 0;

        // 用于比对结果的滑动条变量
        private Vector2 missingKeysScrollPosition;
        private Vector2 extraKeysScrollPosition;

        // Key库相关变量
        [System.Serializable]
        public class KeyLibrary
        {
            public Dictionary<string, string> keyValuePairs = new Dictionary<string, string>();
        }
        
        private KeyLibrary keyLibrary = new KeyLibrary();
        private string keyLibraryPath = "Assets/WorkRecords/output.json";
        private string searchChineseText = "";
        private List<KeyValuePair<string, string>> searchResults = new List<KeyValuePair<string, string>>();
        private Vector2 searchResultsScrollPosition;
        private bool keyLibraryLoaded = false;

        // 组件列表
        private List<LanguageComponentInfo> foundComponents = new List<LanguageComponentInfo>();

        public class LanguageComponentInfo
        {
            public enum ComponentType { LanguageText, LanguageFormatText }
            
            public ComponentType type;
            public MonoBehaviour component;
            public GameObject gameObject;
            public string languageKey;
            public string path;
            public string formatKey;
        }

        private void OnEnable()
        {
            LoadConfigFile();
            TryLoadKeyLibrary();
            UpdateCurrentPrefabName();
        }

        private void OnGUI()
        {
            GUILayout.Label("多语言Key高级管理工具", EditorStyles.boldLabel);
            EditorGUILayout.Space();

            if (!IsInPrefabMode())
            {
                EditorGUILayout.HelpBox("请在预制体编辑模式下使用此工具。", MessageType.Warning);
                return;
            }

            UpdateCurrentPrefabName();

            string[] tabs = { "Key比对与管理", "Key搜索" };
            selectedTab = GUILayout.Toolbar(selectedTab, tabs);
            EditorGUILayout.Space();

            switch (selectedTab)
            {
                case 0:
                    DrawComparisonTab();
                    break;
                case 1:
                    DrawKeySearchTab();
                    break;
            }
        }

        private void DrawComparisonTab()
        {
            // 当前预制体信息
            EditorGUILayout.LabelField("当前预制体信息", EditorStyles.boldLabel);
            EditorGUILayout.LabelField($"预制体名称: {currentPrefabName}");

            // 显示配置文件状态
            if (allPrefabsConfig.prefabs != null && allPrefabsConfig.prefabs.Count > 0)
            {
                EditorGUILayout.HelpBox($"已加载配置文件，包含 {allPrefabsConfig.prefabs.Count} 个预制体", MessageType.Info);

                // 自动加载当前预制体的配置
                LoadCurrentPrefabConfig();
            }

            // Key列表输入区域
            EditorGUILayout.Space();
            EditorGUILayout.LabelField("预制体需要的Key列表", EditorStyles.boldLabel);
            EditorGUILayout.HelpBox("输入或编辑此预制体应该有的所有Key（每行一个）", MessageType.Info);

            EditorGUILayout.BeginVertical(EditorStyles.helpBox);
            {
                keyListInput = EditorGUILayout.TextArea(keyListInput, GUILayout.Height(150));
            }
            EditorGUILayout.EndVertical();

            EditorGUILayout.BeginHorizontal();
            {
                if (GUILayout.Button("清空输入", GUILayout.Width(100)))
                {
                    keyListInput = "";
                }

                if (GUILayout.Button("保存配置", GUILayout.Width(100)))
                {
                    SaveCurrentPrefabToConfig();
                }
                
                if (GUILayout.Button("从Key库选择", GUILayout.Width(100)))
                {
                    selectedTab = 1; // 切换到搜索标签页
                    EditorUtility.DisplayDialog("提示", "请切换到Key搜索标签页查找并添加Key", "确定");
                }
            }
            EditorGUILayout.EndHorizontal();

            // 提取和比对合并的按钮
            EditorGUILayout.Space();
            EditorGUILayout.LabelField("Key比对功能", EditorStyles.boldLabel);

            if (GUILayout.Button("提取并比对Key", GUILayout.Width(150)))
            {
                ExtractAndCompareKeys();
            }

            // 显示提取的Key（仅用于查看）
            if (extractedKeys.Count > 0)
            {
                EditorGUILayout.Space();
                EditorGUILayout.LabelField($"预制体中已有的Key（{extractedKeyCount}个）:", EditorStyles.boldLabel);

                extractedKeysScrollPosition = EditorGUILayout.BeginScrollView(extractedKeysScrollPosition, GUILayout.Height(120));
                {
                    EditorGUILayout.BeginVertical(EditorStyles.helpBox);
                    {
                        foreach (var key in extractedKeys)
                        {
                            EditorGUILayout.LabelField($"{key} - {GetChineseTextFromKey(key)}");
                        }
                    }
                    EditorGUILayout.EndVertical();
                }
                EditorGUILayout.EndScrollView();
            }

            // 显示比对结果
            if (missingKeys.Count > 0 || extraKeys.Count > 0)
            {
                EditorGUILayout.Space();
                EditorGUILayout.LabelField("比对结果", EditorStyles.boldLabel);

                if (missingKeys.Count > 0)
                {
                    EditorGUILayout.HelpBox($"缺少 {missingKeys.Count} 个Key", MessageType.Warning);
                    missingKeysScrollPosition = EditorGUILayout.BeginScrollView(missingKeysScrollPosition, GUILayout.Height(100));
                    {
                        EditorGUILayout.BeginVertical(EditorStyles.helpBox);
                        {
                            foreach (var key in missingKeys)
                            {
                                string chineseText = GetChineseTextFromKey(key);
                                EditorGUILayout.BeginHorizontal();
                                {
                                    EditorGUILayout.LabelField($"缺少: {key}", GUILayout.Width(300));
                                    EditorGUILayout.LabelField($"{chineseText}", EditorStyles.wordWrappedLabel);
                                    
                                    if (GUILayout.Button("复制", GUILayout.Width(50)))
                                    {
                                        EditorGUIUtility.systemCopyBuffer = key;
                                        Debug.Log($"已复制Key: {key}");
                                    }
                                }
                                EditorGUILayout.EndHorizontal();
                            }
                        }
                        EditorGUILayout.EndVertical();
                    }
                    EditorGUILayout.EndScrollView();
                }

                if (extraKeys.Count > 0)
                {
                    EditorGUILayout.HelpBox($"多出 {extraKeys.Count} 个Key", MessageType.Info);
                    extraKeysScrollPosition = EditorGUILayout.BeginScrollView(extraKeysScrollPosition, GUILayout.Height(100));
                    {
                        EditorGUILayout.BeginVertical(EditorStyles.helpBox);
                        {
                            foreach (var key in extraKeys)
                            {
                                string chineseText = GetChineseTextFromKey(key);
                                EditorGUILayout.BeginHorizontal();
                                {
                                    EditorGUILayout.LabelField($"多余: {key}", GUILayout.Width(300));
                                    EditorGUILayout.LabelField($"{chineseText}", EditorStyles.wordWrappedLabel);
                                    
                                    if (GUILayout.Button("复制", GUILayout.Width(50)))
                                    {
                                        EditorGUIUtility.systemCopyBuffer = key;
                                        Debug.Log($"已复制Key: {key}");
                                    }
                                    
                                    if (GUILayout.Button("移除", GUILayout.Width(50)))
                                    {
                                        if (EditorUtility.DisplayDialog("确认", $"确定从预制体中移除Key: {key} 吗？", "确定", "取消"))
                                        {
                                            RemoveKeyFromPrefab(key);
                                        }
                                    }
                                }
                                EditorGUILayout.EndHorizontal();
                            }
                        }
                        EditorGUILayout.EndVertical();
                    }
                    EditorGUILayout.EndScrollView();
                }
            }
        }

        private void DrawKeySearchTab()
        {
            EditorGUILayout.LabelField("Key库搜索功能", EditorStyles.boldLabel);
            
            // Key库文件路径设置
            EditorGUILayout.BeginHorizontal();
            {
                EditorGUILayout.LabelField("Key库路径:", GUILayout.Width(80));
                keyLibraryPath = EditorGUILayout.TextField(keyLibraryPath);
                
                if (GUILayout.Button("浏览", GUILayout.Width(60)))
                {
                    string newPath = EditorUtility.OpenFilePanel("选择Key库JSON文件", 
                        Path.GetDirectoryName(keyLibraryPath), "json");
                    if (!string.IsNullOrEmpty(newPath))
                    {
                        keyLibraryPath = newPath.Replace(Application.dataPath, "Assets");
                    }
                }
            }
            EditorGUILayout.EndHorizontal();

            // Key库加载状态和按钮
            EditorGUILayout.BeginHorizontal();
            {
                if (GUILayout.Button(keyLibraryLoaded ? "重新加载Key库" : "加载Key库", GUILayout.Width(120)))
                {
                    LoadKeyLibrary();
                }
                
                if (keyLibraryLoaded)
                {
                    EditorGUILayout.LabelField($"已加载 {keyLibrary.keyValuePairs.Count} 个Key", EditorStyles.boldLabel);
                }
                else
                {
                    EditorGUILayout.HelpBox("Key库未加载", MessageType.Warning);
                }
            }
            EditorGUILayout.EndHorizontal();

            EditorGUILayout.Space();
            
            // 搜索功能
            EditorGUILayout.LabelField("搜索功能", EditorStyles.boldLabel);
            EditorGUILayout.HelpBox("输入中文文本搜索对应的Key", MessageType.Info);
            
            EditorGUILayout.BeginHorizontal();
            {
                searchChineseText = EditorGUILayout.TextField("搜索:", searchChineseText);
                
                if (GUILayout.Button("搜索", GUILayout.Width(60)))
                {
                    if (!keyLibraryLoaded)
                    {
                        EditorUtility.DisplayDialog("提示", "请先加载Key库", "确定");
                        return;
                    }
                    
                    if (string.IsNullOrEmpty(searchChineseText))
                    {
                        EditorUtility.DisplayDialog("提示", "请输入搜索文本", "确定");
                        return;
                    }
                    
                    SearchKeysByChinese();
                }
                
                if (GUILayout.Button("清空", GUILayout.Width(60)))
                {
                    searchChineseText = "";
                    searchResults.Clear();
                }
            }
            EditorGUILayout.EndHorizontal();

            // 显示搜索结果
            if (searchResults.Count > 0)
            {
                EditorGUILayout.Space();
                EditorGUILayout.LabelField($"搜索结果 ({searchResults.Count} 个):", EditorStyles.boldLabel);
                
                searchResultsScrollPosition = EditorGUILayout.BeginScrollView(searchResultsScrollPosition);
                {
                    foreach (var result in searchResults)
                    {
                        DrawSearchResultItem(result.Key, result.Value);
                    }
                }
                EditorGUILayout.EndScrollView();
            }
            else if (!string.IsNullOrEmpty(searchChineseText) && keyLibraryLoaded)
            {
                EditorGUILayout.HelpBox("未找到匹配的Key", MessageType.Info);
            }

            // 快速操作区域
            if (searchResults.Count > 0)
            {
                EditorGUILayout.Space();
                EditorGUILayout.LabelField("快速操作", EditorStyles.boldLabel);
                
                if (GUILayout.Button("复制第一个结果的Key", GUILayout.Width(150)))
                {
                    if (searchResults.Count > 0)
                    {
                        EditorGUIUtility.systemCopyBuffer = searchResults[0].Key;
                        Debug.Log($"已复制Key: {searchResults[0].Key}");
                    }
                }
            }
        }

        private void DrawSearchResultItem(string key, string chineseText)
        {
            EditorGUILayout.BeginVertical(EditorStyles.helpBox);
            {
                EditorGUILayout.BeginHorizontal();
                {
                    // Key显示区域
                    EditorGUILayout.BeginVertical(GUILayout.Width(position.width * 0.6f));
                    {
                        EditorGUILayout.LabelField($"Key:", EditorStyles.boldLabel);
                        EditorGUILayout.TextField(key, EditorStyles.textField);
                    }
                    EditorGUILayout.EndVertical();

                    // 中文文本显示区域
                    EditorGUILayout.BeginVertical(GUILayout.Width(position.width * 0.3f));
                    {
                        EditorGUILayout.LabelField($"中文:", EditorStyles.boldLabel);
                        EditorGUILayout.LabelField(chineseText, EditorStyles.wordWrappedLabel);
                    }
                    EditorGUILayout.EndVertical();
                }
                EditorGUILayout.EndHorizontal();

                // 操作按钮
                EditorGUILayout.BeginHorizontal();
                {
                    if (GUILayout.Button("复制Key", GUILayout.Width(80)))
                    {
                        EditorGUIUtility.systemCopyBuffer = key;
                        Debug.Log($"已复制Key: {key}");
                    }
                    
                    if (GUILayout.Button("添加到输入框", GUILayout.Width(100)))
                    {
                        AddKeyToInputField(key);
                    }
                    
                    if (GUILayout.Button("查看详情", GUILayout.Width(80)))
                    {
                        ShowKeyDetail(key, chineseText);
                    }
                }
                EditorGUILayout.EndHorizontal();
            }
            EditorGUILayout.EndVertical();
            EditorGUILayout.Space(5);
        }

        private void AddKeyToInputField(string key)
        {
            // 切换到Key比对与管理标签页
            selectedTab = 0;
            
            // 检查是否已存在该Key
            string[] existingKeys = keyListInput.Split(new[] { '\n', '\r' }, StringSplitOptions.RemoveEmptyEntries);
            if (Array.Exists(existingKeys, k => k.Trim() == key))
            {
                EditorUtility.DisplayDialog("提示", "该Key已存在", "确定");
                return;
            }
            
            // 添加Key到输入框
            if (!string.IsNullOrEmpty(keyListInput) && !keyListInput.EndsWith("\n"))
            {
                keyListInput += "\n";
            }
            keyListInput += key + "\n";
            
            Debug.Log($"已添加Key到输入框: {key}");
            EditorUtility.DisplayDialog("成功", $"已添加Key到输入框: {key}", "确定");
        }

        private void ShowKeyDetail(string key, string chineseText)
        {
            string message = $"Key: {key}\n\n";
            message += $"中文文本: {chineseText}\n\n";
            
            // 检查是否在当前预制体的Key列表中
            if (!string.IsNullOrEmpty(keyListInput))
            {
                string[] existingKeys = keyListInput.Split(new[] { '\n', '\r' }, StringSplitOptions.RemoveEmptyEntries);
                bool exists = Array.Exists(existingKeys, k => k.Trim() == key);
                message += $"在当前预制体中: {(exists ? "✓ 已存在" : "✗ 不存在")}\n";
            }
            
            // 检查是否在提取的Key列表中
            bool inExtractedKeys = extractedKeys.Contains(key);
            message += $"在预制体实际Key中: {(inExtractedKeys ? "✓ 已存在" : "✗ 不存在")}";
            
            EditorUtility.DisplayDialog("Key详情", message, "确定");
        }

        // 以下是共享的方法实现
        private void UpdateCurrentPrefabName()
        {
            var prefabRoot = GetCurrentPrefabRoot();
            if (prefabRoot != null)
            {
                currentPrefabName = prefabRoot.name;
            }
            else
            {
                currentPrefabName = "未知预制体";
            }
        }

        private void LoadCurrentPrefabConfig()
        {
            if (allPrefabsConfig.prefabs == null || allPrefabsConfig.prefabs.Count == 0) return;

            PrefabKeyData currentPrefabData = allPrefabsConfig.prefabs.Find(p => p.prefabName == currentPrefabName);
            if (currentPrefabData != null && currentPrefabData.requiredKeys.Count > 0)
            {
                if (string.IsNullOrEmpty(keyListInput))
                {
                    keyListInput = string.Join("\n", currentPrefabData.requiredKeys);
                }
            }
        }

        private void ExtractAndCompareKeys()
        {
            // 1. 首先提取预制体中的所有Key
            FindAllLanguageComponents();

            // 清空之前的提取结果
            extractedKeys.Clear();

            // 提取所有非空Key（不重复）
            foreach (var componentInfo in foundComponents)
            {
                if (!string.IsNullOrEmpty(componentInfo.languageKey) && !extractedKeys.Contains(componentInfo.languageKey))
                {
                    extractedKeys.Add(componentInfo.languageKey);
                }
                
                if (componentInfo.type == LanguageComponentInfo.ComponentType.LanguageFormatText && 
                    !string.IsNullOrEmpty(componentInfo.formatKey) && !extractedKeys.Contains(componentInfo.formatKey))
                {
                    extractedKeys.Add(componentInfo.formatKey);
                }
            }

            extractedKeyCount = extractedKeys.Count;
            Debug.Log($"从当前预制体中提取了 {extractedKeyCount} 个Key");

            // 2. 如果没有输入Key列表，则使用已加载的配置或提示
            if (string.IsNullOrEmpty(keyListInput))
            {
                LoadCurrentPrefabConfig();

                if (string.IsNullOrEmpty(keyListInput))
                {
                    EditorUtility.DisplayDialog("提示", "请先在输入框中输入预制体需要的Key列表", "确定");
                    return;
                }
            }

            // 3. 进行比对
            CompareKeys();
        }

        private void CompareKeys()
        {
            string[] requiredKeys = keyListInput.Split(new[] { '\n', '\r' }, StringSplitOptions.RemoveEmptyEntries);
            List<string> requiredKeyList = new List<string>();
            foreach (var key in requiredKeys)
            {
                string trimmedKey = key.Trim();
                if (!string.IsNullOrEmpty(trimmedKey) && !requiredKeyList.Contains(trimmedKey))
                {
                    requiredKeyList.Add(trimmedKey);
                }
            }

            if (requiredKeyList.Count == 0)
            {
                EditorUtility.DisplayDialog("提示", "请输入有效的Key列表", "确定");
                return;
            }

            List<string> prefabKeys = new List<string>(extractedKeys);

            // 找出缺少的Key
            missingKeys.Clear();
            foreach (var key in requiredKeyList)
            {
                if (!prefabKeys.Contains(key))
                {
                    missingKeys.Add(key);
                }
            }

            // 找出多余的Key
            extraKeys.Clear();
            foreach (var key in prefabKeys)
            {
                if (!requiredKeyList.Contains(key))
                {
                    extraKeys.Add(key);
                }
            }

            string message = $"比对完成:\n";
            message += $"预制体中的Key数量: {prefabKeys.Count}\n";
            message += $"需要的Key数量: {requiredKeyList.Count}\n";
            message += $"缺少的Key数量: {missingKeys.Count}\n";
            message += $"多余的Key数量: {extraKeys.Count}";

            EditorUtility.DisplayDialog("比对结果", message, "确定");
            Debug.Log(message);
            Repaint();
        }

        private void LoadConfigFile()
        {
            string defaultPath = "Assets/PrefabKeyConfigs/AllPrefabsKeys.json";

            if (!File.Exists(defaultPath))
            {
                allPrefabsConfig = new AllPrefabsKeyConfig();
                Debug.Log("配置文件不存在，已创建新配置");
                return;
            }

            try
            {
                jsonFilePath = defaultPath;
                string jsonContent = File.ReadAllText(jsonFilePath, Encoding.UTF8);
                allPrefabsConfig = JsonUtility.FromJson<AllPrefabsKeyConfig>(jsonContent);

                if (allPrefabsConfig.prefabs == null)
                {
                    allPrefabsConfig.prefabs = new List<PrefabKeyData>();
                }

                Debug.Log($"已自动加载配置文件: {jsonFilePath}");
                Debug.Log($"包含 {allPrefabsConfig.prefabs.Count} 个预制体");
            }
            catch (Exception e)
            {
                Debug.LogError($"加载配置文件失败: {e.Message}");
                allPrefabsConfig = new AllPrefabsKeyConfig();
            }
        }

        private void SaveCurrentPrefabToConfig()
        {
            if (string.IsNullOrEmpty(keyListInput))
            {
                EditorUtility.DisplayDialog("提示", "请先输入Key列表", "确定");
                return;
            }

            string[] requiredKeys = keyListInput.Split(new[] { '\n', '\r' }, StringSplitOptions.RemoveEmptyEntries);
            List<string> requiredKeyList = new List<string>();
            foreach (var key in requiredKeys)
            {
                string trimmedKey = key.Trim();
                if (!string.IsNullOrEmpty(trimmedKey) && !requiredKeyList.Contains(trimmedKey))
                {
                    requiredKeyList.Add(trimmedKey);
                }
            }

            if (requiredKeyList.Count == 0)
            {
                EditorUtility.DisplayDialog("提示", "Key列表为空", "确定");
                return;
            }

            if (allPrefabsConfig.prefabs == null)
            {
                allPrefabsConfig.prefabs = new List<PrefabKeyData>();
            }

            PrefabKeyData prefabData = allPrefabsConfig.prefabs.Find(p => p.prefabName == currentPrefabName);
            if (prefabData == null)
            {
                prefabData = new PrefabKeyData
                {
                    prefabName = currentPrefabName,
                    requiredKeys = requiredKeyList,
                    lastModified = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"),
                    keyCount = requiredKeyList.Count
                };
                allPrefabsConfig.prefabs.Add(prefabData);
                Debug.Log($"添加了新预制体 '{currentPrefabName}' 到配置");
            }
            else
            {
                prefabData.requiredKeys = requiredKeyList;
                prefabData.lastModified = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
                prefabData.keyCount = requiredKeyList.Count;
                Debug.Log($"更新了预制体 '{currentPrefabName}' 的配置");
            }

            allPrefabsConfig.totalPrefabs = allPrefabsConfig.prefabs.Count;
            allPrefabsConfig.totalKeys = 0;
            foreach (var prefab in allPrefabsConfig.prefabs)
            {
                allPrefabsConfig.totalKeys += prefab.keyCount;
            }
            allPrefabsConfig.lastModified = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");

            SaveConfigToFile();
        }

        private void SaveConfigToFile()
        {
            try
            {
                string directory = Path.GetDirectoryName(jsonFilePath);
                if (!Directory.Exists(directory))
                {
                    Directory.CreateDirectory(directory);
                }

                string json = JsonUtility.ToJson(allPrefabsConfig, true);
                File.WriteAllText(jsonFilePath, json, Encoding.UTF8);
                AssetDatabase.Refresh();

                Debug.Log($"配置文件已保存: {jsonFilePath}");
                Debug.Log($"包含 {allPrefabsConfig.totalPrefabs} 个预制体，总计 {allPrefabsConfig.totalKeys} 个Key");

                EditorUtility.DisplayDialog("成功",
                    $"配置文件已保存:\n{jsonFilePath}\n" +
                    $"包含 {allPrefabsConfig.totalPrefabs} 个预制体\n" +
                    $"总计 {allPrefabsConfig.totalKeys} 个Key",
                    "确定");
            }
            catch (Exception e)
            {
                Debug.LogError($"保存配置文件失败: {e.Message}");
                EditorUtility.DisplayDialog("错误", $"保存配置文件失败:\n{e.Message}", "确定");
            }
        }

        private void FindAllLanguageComponents()
        {
            foundComponents.Clear();

            var prefabRoot = GetCurrentPrefabRoot();
            if (prefabRoot == null)
            {
                Debug.LogError("无法获取预制体根对象");
                return;
            }

            LanguageText[] languageTexts = prefabRoot.GetComponentsInChildren<LanguageText>(true);
            foreach (var languageText in languageTexts)
            {
                string languageKey = GetLanguageKeyFromComponent(languageText);
                
                var info = new LanguageComponentInfo
                {
                    type = LanguageComponentInfo.ComponentType.LanguageText,
                    component = languageText,
                    gameObject = languageText.gameObject,
                    languageKey = languageKey,
                    path = GetGameObjectPath(languageText.transform, prefabRoot.transform)
                };

                foundComponents.Add(info);
            }

            try
            {
                var formatTexts = prefabRoot.GetComponentsInChildren<LanguageFormatText>(true);
                Debug.Log($"找到 {formatTexts.Length} 个LanguageFormatText组件");
                
                foreach (var formatText in formatTexts)
                {
                    string languageKey = GetLanguageKeyFromComponent(formatText);
                    
                    var info = new LanguageComponentInfo
                    {
                        type = LanguageComponentInfo.ComponentType.LanguageFormatText,
                        component = formatText,
                        gameObject = formatText.gameObject,
                        languageKey = languageKey,
                        path = GetGameObjectPath(formatText.transform, prefabRoot.transform),
                        formatKey = GetFormatKeyFromComponent(formatText)
                    };

                    foundComponents.Add(info);
                }
            }
            catch (Exception e)
            {
                Debug.LogError($"查找LanguageFormatText组件时出错: {e.Message}");
            }

            Debug.Log($"找到 {foundComponents.Count} 个多语言组件");
        }

        private void RemoveKeyFromPrefab(string key)
        {
            if (string.IsNullOrEmpty(key))
            {
                Debug.LogWarning("要移除的Key为空");
                return;
            }
            
            FindAllLanguageComponents();
            
            int removedCount = 0;
            foreach (var componentInfo in foundComponents)
            {
                if (componentInfo.languageKey == key)
                {
                    try
                    {
                        var serializedObject = new SerializedObject(componentInfo.component);
                        Undo.RegisterCompleteObjectUndo(componentInfo.component, "Remove Key");
                        
                        var textProperty = serializedObject.FindProperty("m_Text");
                        var keyProperty = serializedObject.FindProperty("m_languageKey");
                        
                        if (textProperty != null)
                        {
                            textProperty.stringValue = "";
                        }
                        
                        if (keyProperty != null)
                        {
                            keyProperty.stringValue = "";
                        }
                        
                        serializedObject.ApplyModifiedProperties();
                        EditorUtility.SetDirty(componentInfo.component);
                        removedCount++;
                        Debug.Log($"已从 {componentInfo.path} 移除Key: {key}");
                    }
                    catch (Exception e)
                    {
                        Debug.LogError($"移除Key {key} 时出错: {e.Message}");
                    }
                }
            }
            
            var prefabRoot = GetCurrentPrefabRoot();
            if (prefabRoot != null)
            {
                EditorUtility.SetDirty(prefabRoot);
                PrefabUtility.SavePrefabAsset(prefabRoot);
            }
            
            if (removedCount > 0)
            {
                ExtractAndCompareKeys();
                Debug.Log($"成功移除了 {removedCount} 个Key: {key}");
                EditorUtility.DisplayDialog("成功", $"已移除 {removedCount} 个Key: {key}", "确定");
            }
            else
            {
                Debug.Log($"未找到Key: {key}");
                EditorUtility.DisplayDialog("提示", $"未在预制体中找到Key: {key}", "确定");
            }
        }

        // Key库相关方法
        private void TryLoadKeyLibrary()
        {
            string[] possiblePaths = {
                "Assets/Resources/LanguageKeyLibrary.json",
                "Assets/LanguageKeyLibrary.json",
                "Assets/Config/LanguageKeyLibrary.json",
                "Assets/Data/LanguageKeyLibrary.json",
                "Assets/WorkRecords/output.json"
            };
            
            foreach (string path in possiblePaths)
            {
                if (File.Exists(path))
                {
                    keyLibraryPath = path;
                    LoadKeyLibrary();
                    return;
                }
            }
            
            Debug.Log("未找到Key库文件，请手动加载");
        }

        private void LoadKeyLibrary()
        {
            if (!File.Exists(keyLibraryPath))
            {
                EditorUtility.DisplayDialog("错误", $"Key库文件不存在:\n{keyLibraryPath}", "确定");
                keyLibraryLoaded = false;
                return;
            }
            
            try
            {
                string jsonContent = File.ReadAllText(keyLibraryPath, Encoding.UTF8);
                jsonContent = jsonContent.Trim();
                
                if (!jsonContent.StartsWith("{"))
                {
                    ParseKeyValuePairsFromText(jsonContent);
                    return;
                }
                
                try
                {
                    ParseSimpleJsonDictionary(jsonContent);
                }
                catch (Exception ex1)
                {
                    Debug.LogWarning($"标准JSON解析失败，尝试替代方法: {ex1.Message}");
                    ParseKeyValuePairsFromText(jsonContent);
                }
            }
            catch (Exception e)
            {
                Debug.LogError($"加载Key库失败: {e.Message}");
                EditorUtility.DisplayDialog("错误", $"加载Key库失败:\n{e.Message}", "确定");
                keyLibraryLoaded = false;
            }
        }

        private void ParseSimpleJsonDictionary(string jsonContent)
        {
            jsonContent = jsonContent.Trim();
            if (jsonContent.StartsWith("{") && jsonContent.EndsWith("}"))
            {
                jsonContent = jsonContent.Substring(1, jsonContent.Length - 2).Trim();
            }
            
            keyLibrary.keyValuePairs = new Dictionary<string, string>();
            
            var lines = jsonContent.Split(new[] { ',' }, StringSplitOptions.RemoveEmptyEntries);
            
            foreach (var line in lines)
            {
                try
                {
                    var parts = line.Split(new[] { ':' }, 2);
                    if (parts.Length == 2)
                    {
                        string key = parts[0].Trim().Trim('"', '\'', ' ');
                        string value = parts[1].Trim().Trim('"', '\'', ' ');
                        
                        key = key.Replace("\\\"", "\"");
                        value = value.Replace("\\\"", "\"");
                        
                        if (!string.IsNullOrEmpty(key) && !string.IsNullOrEmpty(value))
                        {
                            if (!keyLibrary.keyValuePairs.ContainsKey(key))
                            {
                                keyLibrary.keyValuePairs.Add(key, value);
                            }
                        }
                    }
                }
                catch (Exception ex)
                {
                    Debug.LogWarning($"解析行失败: {line}\n错误: {ex.Message}");
                }
            }
            
            keyLibraryLoaded = true;
            Debug.Log($"成功加载Key库: {keyLibraryPath}");
            Debug.Log($"包含 {keyLibrary.keyValuePairs.Count} 个Key");
        }

        private void ParseKeyValuePairsFromText(string text)
        {
            keyLibrary.keyValuePairs = new Dictionary<string, string>();
            
            string pattern = @"\""([^\""]+)\""\s*:\s*\""([^\""]+)\""";
            var matches = System.Text.RegularExpressions.Regex.Matches(text, pattern);
            
            if (matches.Count > 0)
            {
                foreach (System.Text.RegularExpressions.Match match in matches)
                {
                    if (match.Groups.Count == 3)
                    {
                        string key = match.Groups[1].Value;
                        string value = match.Groups[2].Value;
                        
                        if (!keyLibrary.keyValuePairs.ContainsKey(key))
                        {
                            keyLibrary.keyValuePairs.Add(key, value);
                        }
                    }
                }
            }
            else
            {
                ParseAlternativeFormat(text);
            }
            
            keyLibraryLoaded = true;
            Debug.Log($"成功解析Key库: {keyLibraryPath}");
            Debug.Log($"包含 {keyLibrary.keyValuePairs.Count} 个Key");
        }

        private void ParseAlternativeFormat(string text)
        {
            var lines = text.Split(new[] { '\n', '\r' }, StringSplitOptions.RemoveEmptyEntries);
            
            foreach (var line in lines)
            {
                try
                {
                    var trimmedLine = line.Trim();
                    
                    if (trimmedLine.StartsWith("//") || trimmedLine.StartsWith("#") || trimmedLine.StartsWith("/*"))
                        continue;
                    
                    if (trimmedLine == "{" || trimmedLine == "}")
                        continue;
                    
                    char[] separators = { ':', '=' };
                    
                    foreach (char separator in separators)
                    {
                        var parts = trimmedLine.Split(new[] { separator }, 2);
                        if (parts.Length == 2)
                        {
                            string key = parts[0].Trim().Trim('"', '\'', ' ', '\t');
                            string value = parts[1].Trim().Trim('"', '\'', ' ', '\t', ',');
                            
                            if (value.EndsWith(";"))
                                value = value.Substring(0, value.Length - 1);
                            
                            if (!string.IsNullOrEmpty(key) && !string.IsNullOrEmpty(value))
                            {
                                if (!keyLibrary.keyValuePairs.ContainsKey(key))
                                {
                                    keyLibrary.keyValuePairs.Add(key, value);
                                }
                                break;
                            }
                        }
                    }
                }
                catch (Exception ex)
                {
                    Debug.LogWarning($"解析行失败: {line}\n错误: {ex.Message}");
                }
            }
        }
        
        private void SearchKeysByChinese()
        {
            searchResults.Clear();
            
            string searchText = searchChineseText.ToLower();
            
            foreach (var kvp in keyLibrary.keyValuePairs)
            {
                if (kvp.Value.ToLower().Contains(searchText))
                {
                    searchResults.Add(kvp);
                }
            }
            
            searchResults.Sort((a, b) =>
            {
                bool aExact = a.Value == searchChineseText;
                bool bExact = b.Value == searchChineseText;
                
                if (aExact && !bExact) return -1;
                if (!aExact && bExact) return 1;
                
                return a.Value.Length.CompareTo(b.Value.Length);
            });
            
            Debug.Log($"找到 {searchResults.Count} 个匹配的Key");
        }

        private string GetChineseTextFromKey(string key)
        {
            if (!keyLibraryLoaded || keyLibrary == null || keyLibrary.keyValuePairs == null)
            {
                return "(Key库未加载)";
            }
            
            if (string.IsNullOrEmpty(key))
            {
                return "(空Key)";
            }
            
            if (keyLibrary.keyValuePairs.TryGetValue(key, out string chineseText))
            {
                return chineseText;
            }
            else
            {
                foreach (var kvp in keyLibrary.keyValuePairs)
                {
                    if (kvp.Key.Equals(key, StringComparison.OrdinalIgnoreCase))
                    {
                        return kvp.Value + " (大小写不匹配)";
                    }
                }
                return "(Key库中未找到)";
            }
        }

        // 辅助方法
        private string GetLanguageKeyFromComponent(Component component)
        {
            if (component == null) return "";
            
            try
            {
                var serializedObject = new SerializedObject(component);
                var keyProperty = serializedObject.FindProperty("m_languageKey");
                
                if (keyProperty != null && !string.IsNullOrEmpty(keyProperty.stringValue))
                {
                    return keyProperty.stringValue;
                }
            }
            catch (Exception e)
            {
                Debug.LogWarning($"获取LanguageKey时出错: {e.Message}");
            }
            
            return "";
        }

        private string GetFormatKeyFromComponent(Component component)
        {
            if (component == null) return "";
            
            try
            {
                var serializedObject = new SerializedObject(component);
                var formatKeyProperty = serializedObject.FindProperty("formatKey");
                
                if (formatKeyProperty != null && !string.IsNullOrEmpty(formatKeyProperty.stringValue))
                {
                    return formatKeyProperty.stringValue;
                }
            }
            catch (Exception e)
            {
                Debug.LogWarning($"获取FormatKey时出错: {e.Message}");
            }
            
            return "";
        }

        private string GetGameObjectPath(Transform obj, Transform root)
        {
            if (obj == null || root == null) return "未知路径";

            string path = obj.name;
            Transform current = obj.parent;

            while (current != null && current != root && current != root.parent)
            {
                path = current.name + "/" + path;
                current = current.parent;
            }

            return path;
        }

        private bool IsInPrefabMode()
        {
            try
            {
                var prefabStage = PrefabStageUtility.GetCurrentPrefabStage();
                return prefabStage != null;
            }
            catch
            {
                GameObject selected = Selection.activeGameObject;
                if (selected != null)
                {
                    return UnityEditor.PrefabUtility.IsPartOfAnyPrefab(selected);
                }
                return false;
            }
        }

        private GameObject GetCurrentPrefabRoot()
        {
            try
            {
                var prefabStage = PrefabStageUtility.GetCurrentPrefabStage();
                return prefabStage?.prefabContentsRoot;
            }
            catch
            {
                GameObject selected = Selection.activeGameObject;
                if (selected != null && UnityEditor.PrefabUtility.IsPartOfAnyPrefab(selected))
                {
                    return UnityEditor.PrefabUtility.GetOutermostPrefabInstanceRoot(selected);
                }
                return null;
            }
        }
    }
}