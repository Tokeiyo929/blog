using UnityEngine;
using UnityEditor;
using UnityEngine.UI;
using UnityEditor.SceneManagement;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System;

namespace EvonyExtension.Editor
{
    public class LanguageComponentInfo
    {
        public enum ComponentType { LanguageText, LanguageFormatText }
        
        public ComponentType type;
        public MonoBehaviour component;
        public GameObject gameObject;
        public string languageKey;
        public string path;
        public string textContent;
        public string originalText;
        public string formatKey;
        public string chineseText;
    }

    [System.Serializable]
    public class KeyLibrary
    {
        public Dictionary<string, string> keyValuePairs = new Dictionary<string, string>();
    }

    public class LanguageTextBasicTool : EditorWindow
    {
        [MenuItem("Tools/LanguageText/基础工具 - 查找与替换")]
        private static void ShowWindow()
        {
            LanguageTextBasicTool window = GetWindow<LanguageTextBasicTool>("多语言基础工具");
            window.minSize = new Vector2(600, 400);
            window.Show();
        }

        private Vector2 scrollPosition;
        private List<LanguageComponentInfo> foundComponents = new List<LanguageComponentInfo>();
        
        // Key库相关变量
        private KeyLibrary keyLibrary = new KeyLibrary();
        private string keyLibraryPath = "Assets/WorkRecords/output.json";
        private bool keyLibraryLoaded = false;
        
        // 显示模式
        private bool showChineseMode = false;
        
        // 当前预制体名称
        private string currentPrefabName = "";

        private void OnEnable()
        {
            TryLoadKeyLibrary();
            UpdateCurrentPrefabName();
        }

        private void OnGUI()
        {
            GUILayout.Label("多语言文本基础工具", EditorStyles.boldLabel);
            EditorGUILayout.Space();

            if (!IsInPrefabMode())
            {
                EditorGUILayout.HelpBox("请在预制体编辑模式下使用此工具。", MessageType.Warning);
                return;
            }

            UpdateCurrentPrefabName();
            EditorGUILayout.LabelField($"当前预制体: {currentPrefabName}", EditorStyles.boldLabel);
            EditorGUILayout.Space();

            DrawToolbar();
            EditorGUILayout.Space();
            DrawKeyLibraryStatus();
            EditorGUILayout.Space();

            if (foundComponents.Count > 0)
            {
                GUILayout.Label($"找到 {foundComponents.Count} 个多语言组件", EditorStyles.boldLabel);
                scrollPosition = EditorGUILayout.BeginScrollView(scrollPosition);
                {
                    foreach (var componentInfo in foundComponents)
                    {
                        DrawLanguageComponentInfo(componentInfo);
                    }
                }
                EditorGUILayout.EndScrollView();
            }
        }

        private void DrawToolbar()
        {
            EditorGUILayout.BeginHorizontal();
            {
                if (GUILayout.Button("查找所有组件", GUILayout.Width(150)))
                {
                    FindAllLanguageComponents();
                }

                if (GUILayout.Button("替换为Key", GUILayout.Width(150)))
                {
                    ReplaceTextWithKey();
                }

                if (GUILayout.Button("替换为中文", GUILayout.Width(150)))
                {
                    ReplaceTextWithChinese();
                }

                // 显示模式切换
                EditorGUILayout.LabelField("显示:", GUILayout.Width(40));
                bool previousMode = showChineseMode;
                showChineseMode = EditorGUILayout.ToggleLeft("中文", showChineseMode, GUILayout.Width(60));
                
                if (previousMode != showChineseMode)
                {
                    Repaint();
                }
            }
            EditorGUILayout.EndHorizontal();
        }

        private void DrawKeyLibraryStatus()
        {
            EditorGUILayout.BeginHorizontal();
            {
                EditorGUILayout.LabelField("Key库路径:", GUILayout.Width(70));
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
                
                if (GUILayout.Button(keyLibraryLoaded ? "重新加载" : "加载", GUILayout.Width(80)))
                {
                    LoadKeyLibrary();
                }
            }
            EditorGUILayout.EndHorizontal();

            if (keyLibraryLoaded)
            {
                EditorGUILayout.HelpBox($"已加载 {keyLibrary.keyValuePairs.Count} 个Key", MessageType.Info);
            }
            else
            {
                EditorGUILayout.HelpBox("Key库未加载，中文替换功能不可用", MessageType.Warning);
            }
        }

        private void DrawLanguageComponentInfo(LanguageComponentInfo componentInfo)
        {
            EditorGUILayout.BeginVertical(EditorStyles.helpBox);
            {
                EditorGUILayout.BeginHorizontal();
                {
                    // 显示组件类型
                    string typeName = componentInfo.type == LanguageComponentInfo.ComponentType.LanguageText 
                        ? "LanguageText" : "LanguageFormatText";
                    
                    EditorGUILayout.LabelField($"{typeName}:", EditorStyles.boldLabel, GUILayout.Width(100));
                    
                    // 显示Key或中文
                    string displayText = showChineseMode && !string.IsNullOrEmpty(componentInfo.chineseText)
                        ? componentInfo.chineseText
                        : componentInfo.languageKey;
                    
                    EditorGUILayout.LabelField(displayText, GUILayout.Width(250));
                    
                    if (GUILayout.Button("选择", GUILayout.Width(60)))
                    {
                        Selection.activeObject = componentInfo.gameObject;
                        EditorGUIUtility.PingObject(componentInfo.gameObject);
                    }
                }
                EditorGUILayout.EndHorizontal();
                
                // 显示并允许编辑文本内容
                string currentText = GetTextContent(componentInfo.component);
                EditorGUILayout.BeginHorizontal();
                {
                    EditorGUILayout.LabelField("文本:", GUILayout.Width(40));
                    string newText = EditorGUILayout.TextField(currentText);
                    
                    // 如果文本被修改，更新组件
                    if (newText != currentText)
                    {
                        var serializedObject = new SerializedObject(componentInfo.component);
                        var textProperty = serializedObject.FindProperty("m_Text");
                        if (textProperty != null)
                        {
                            Undo.RegisterCompleteObjectUndo(componentInfo.component, "Edit Text");
                            textProperty.stringValue = newText;
                            serializedObject.ApplyModifiedProperties();
                            EditorUtility.SetDirty(componentInfo.component);
                            componentInfo.textContent = newText;
                        }
                    }
                }
                EditorGUILayout.EndHorizontal();
                
                EditorGUILayout.LabelField($"路径: {componentInfo.path}");
                
                // 如果是LanguageFormatText，显示formatKey
                if (componentInfo.type == LanguageComponentInfo.ComponentType.LanguageFormatText && 
                    !string.IsNullOrEmpty(componentInfo.formatKey))
                {
                    EditorGUILayout.LabelField($"格式化Key: {componentInfo.formatKey}");
                }

                if (string.IsNullOrEmpty(componentInfo.languageKey))
                {
                    EditorGUILayout.HelpBox("LanguageKey为空！", MessageType.Warning);
                }
            }
            EditorGUILayout.EndVertical();
            EditorGUILayout.Space(5);
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

            // 查找所有LanguageText组件
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
                    path = GetGameObjectPath(languageText.transform, prefabRoot.transform),
                    textContent = GetTextContent(languageText),
                    originalText = GetTextContent(languageText),
                    chineseText = keyLibraryLoaded ? GetChineseTextFromKey(languageKey) : "(Key库未加载)"
                };

                foundComponents.Add(info);
            }

            // 查找所有LanguageFormatText组件
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
                        textContent = GetTextContent(formatText),
                        originalText = GetTextContent(formatText),
                        formatKey = GetFormatKeyFromComponent(formatText),
                        chineseText = keyLibraryLoaded ? GetChineseTextFromKey(languageKey) : "(Key库未加载)"
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

        private void ReplaceTextWithKey()
        {
            if (foundComponents.Count == 0)
            {
                Debug.LogWarning("请先点击'查找所有组件'按钮");
                return;
            }

            int replacedCount = 0;
            int skippedCount = 0;

            Undo.SetCurrentGroupName("替换文本为Key值");
            int undoGroup = Undo.GetCurrentGroup();

            foreach (var componentInfo in foundComponents)
            {
                if (string.IsNullOrEmpty(componentInfo.languageKey) || componentInfo.component == null)
                {
                    skippedCount++;
                    continue;
                }

                try
                {
                    var serializedObject = new SerializedObject(componentInfo.component);
                    Undo.RegisterCompleteObjectUndo(componentInfo.component, "替换文本为Key值");
                    
                    var textProperty = serializedObject.FindProperty("m_Text");
                    if (textProperty != null)
                    {
                        textProperty.stringValue = componentInfo.languageKey;
                        serializedObject.ApplyModifiedProperties();
                        replacedCount++;
                        componentInfo.textContent = componentInfo.languageKey;
                        EditorUtility.SetDirty(componentInfo.component);
                    }
                }
                catch (Exception e)
                {
                    Debug.LogError($"替换 {componentInfo.path} 的文本时出错: {e.Message}");
                }
            }

            Undo.CollapseUndoOperations(undoGroup);

            var prefabRoot = GetCurrentPrefabRoot();
            if (prefabRoot != null)
            {
                EditorUtility.SetDirty(prefabRoot);
                PrefabUtility.SavePrefabAsset(prefabRoot);
            }

            Debug.Log($"替换完成: {replacedCount} 个文本已替换为Key值, {skippedCount} 个因Key为空被跳过");
            Repaint();
        }

        private void ReplaceTextWithChinese()
        {
            if (!keyLibraryLoaded)
            {
                EditorUtility.DisplayDialog("错误", "请先加载Key库", "确定");
                return;
            }

            if (foundComponents.Count == 0)
            {
                Debug.LogWarning("请先点击'查找所有组件'按钮");
                return;
            }

            int replacedCount = 0;
            int skippedCount = 0;
            int notFoundCount = 0;

            Undo.SetCurrentGroupName("替换文本为中文");
            int undoGroup = Undo.GetCurrentGroup();

            foreach (var componentInfo in foundComponents)
            {
                if (string.IsNullOrEmpty(componentInfo.languageKey) || componentInfo.component == null)
                {
                    skippedCount++;
                    continue;
                }

                try
                {
                    string chineseText = GetChineseTextFromKey(componentInfo.languageKey);
                    
                    // 检查是否找到中文文本
                    if (chineseText.StartsWith("(") && chineseText.EndsWith(")"))
                    {
                        notFoundCount++;
                        continue;
                    }

                    var serializedObject = new SerializedObject(componentInfo.component);
                    Undo.RegisterCompleteObjectUndo(componentInfo.component, "替换文本为中文");
                    
                    var textProperty = serializedObject.FindProperty("m_Text");
                    if (textProperty != null)
                    {
                        textProperty.stringValue = chineseText;
                        serializedObject.ApplyModifiedProperties();
                        replacedCount++;
                        componentInfo.textContent = chineseText;
                        EditorUtility.SetDirty(componentInfo.component);
                    }
                }
                catch (Exception e)
                {
                    Debug.LogError($"替换 {componentInfo.path} 的文本为中文时出错: {e.Message}");
                }
            }

            Undo.CollapseUndoOperations(undoGroup);

            var prefabRoot = GetCurrentPrefabRoot();
            if (prefabRoot != null)
            {
                EditorUtility.SetDirty(prefabRoot);
                PrefabUtility.SavePrefabAsset(prefabRoot);
            }

            string message = $"中文替换完成:\n";
            message += $"- 成功替换: {replacedCount} 个\n";
            message += $"- Key为空跳过: {skippedCount} 个\n";
            message += $"- Key库中未找到: {notFoundCount} 个";

            EditorUtility.DisplayDialog("替换完成", message, "确定");
            Debug.Log(message);
            Repaint();
        }

        private string GetTextContent(Component component)
        {
            if (component == null) return "组件为空";

            try
            {
                var serializedObject = new SerializedObject(component);
                var textProperty = serializedObject.FindProperty("m_Text");
                
                if (textProperty != null)
                {
                    return string.IsNullOrEmpty(textProperty.stringValue) ? "空文本" : textProperty.stringValue;
                }
                
                var textProp = component.GetType().GetProperty("text");
                if (textProp != null)
                {
                    var value = textProp.GetValue(component);
                    if (value != null && !string.IsNullOrEmpty(value.ToString()))
                    {
                        return value.ToString();
                    }
                }
            }
            catch (Exception e)
            {
                Debug.LogWarning($"获取文本内容时出错: {e.Message}");
            }

            return "空文本";
        }

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
    }
}