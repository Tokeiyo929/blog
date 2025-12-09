using UnityEngine;
using UnityEditor;
using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine.UI;

public class PrefabManagerEditor : EditorWindow
{
    // 预制体数据相关
    private List<string> prefabList = new List<string>();
    private List<PrefabData> savedPrefabData = new List<PrefabData>();
    private Dictionary<string, string> prefabIndex = new Dictionary<string, string>();
    private Dictionary<string, bool> categoryFoldoutStates = new Dictionary<string, bool>();

    // UI相关
    private string prefabSearchName = "";
    private Vector2 scrollPosition;

    // 数据保存路径
    private string prefabDataPath;
    private string prefabIndexPath;

    // 预制体搜索路径（相对路径）
    private string prefabSearchRelativePath = "Assets/PackageRes/Raw/Category/Prefabs/UI";

    // ==================== 从 PrefabBuilder 合并的功能 ====================
    // 存储最近导入的图片信息
    private string lastImportedImagePath = "";
    private string lastImportedImageName = "";

    // 图片导入目录
    private string imageImportFolder = "Assets/WorkRecords/UIImage";

    // 默认网络路径
    private string defaultImportPath = @"\\192.168.54.108\美术日常资源\RG项目组\UI\UI迭代-1\5.0";

    // 预览预制体相关变量
    private GameObject previewInstance;
    private bool autoFindCanvas = true;
    private Transform customParent;
    private bool showPreviewSettings = false;

    private void OnEnable()
    {
        // 初始化数据保存路径
        string recordsDir = Path.Combine(Application.dataPath, "WorkRecords");
        prefabDataPath = Path.Combine(recordsDir, "prefab_data.json");
        prefabIndexPath = Path.Combine(recordsDir, "prefab_index.json");

        // 加载保存的数据
        LoadPrefabData();
        LoadPrefabIndex();
        SyncPrefabListFromSavedData();
    }

    private void OnGUI()
    {
        scrollPosition = EditorGUILayout.BeginScrollView(scrollPosition);

        DrawPrefabPreviewSection();
        GUILayout.Space(20);
        DrawImageImportSection();
        GUILayout.Space(20);
        DrawPrefabManagementSection();

        EditorGUILayout.EndScrollView();
    }
    public void CallOnGUI()
    {
        // 保存原始scrollPosition
        var originalScrollPosition = scrollPosition;

        // 调用原始的OnGUI逻辑
        OnGUI();

        // 恢复scrollPosition
        scrollPosition = originalScrollPosition;
    }

    // ==================== 预览UI预制体功能 ====================
    private void DrawPrefabPreviewSection()
    {
        GUILayout.Label("预览UI预制体（美术专用）", EditorStyles.boldLabel);
        EditorGUILayout.HelpBox("可以直接预览任何UI预制体，无需Window组件", MessageType.Info);

        EditorGUILayout.BeginHorizontal();
        if (GUILayout.Button("预览选中的预制体", GUILayout.Height(30)))
        {
            PreviewSelectedPrefab();
        }

        EditorGUI.BeginDisabledGroup(previewInstance == null);
        if (GUILayout.Button("关闭预览", GUILayout.Width(100), GUILayout.Height(30)))
        {
            ClosePreview();
        }
        EditorGUI.EndDisabledGroup();
        EditorGUILayout.EndHorizontal();

        // 预览设置
        showPreviewSettings = EditorGUILayout.Foldout(showPreviewSettings, "预览设置");
        if (showPreviewSettings)
        {
            EditorGUI.indentLevel++;
            autoFindCanvas = EditorGUILayout.Toggle("自动查找Canvas", autoFindCanvas);

            if (!autoFindCanvas)
            {
                customParent = (Transform)EditorGUILayout.ObjectField("父节点", customParent, typeof(Transform), true);
            }

            EditorGUILayout.HelpBox("使用说明：\n1. 在Project窗口选择一个UI预制体\n2. 点击'预览选中的预制体'\n3. 进入播放模式查看效果", MessageType.Info);
            EditorGUI.indentLevel--;
        }

        // 显示当前预览状态
        if (previewInstance != null)
        {
            EditorGUILayout.BeginVertical(EditorStyles.helpBox);
            EditorGUILayout.LabelField("当前预览:", EditorStyles.boldLabel);
            EditorGUILayout.ObjectField("实例对象", previewInstance, typeof(GameObject), true);
            EditorGUILayout.EndVertical();
        }
    }

    // ==================== 图片导入功能 ====================
    private void DrawImageImportSection()
    {
        GUILayout.Label("图片导入", EditorStyles.boldLabel);

        EditorGUILayout.BeginHorizontal();
        if (GUILayout.Button("导入图片并创建UI Image"))
        {
            ImportImageAndCreateUI();
        }

        // 添加删除按钮，只有有导入记录时才启用
        EditorGUI.BeginDisabledGroup(string.IsNullOrEmpty(lastImportedImagePath));
        if (GUILayout.Button("删除UIImage文件夹和对象", GUILayout.Width(180)))
        {
            DeleteUIImageFolderAndObject();
        }
        EditorGUI.EndDisabledGroup();
        EditorGUILayout.EndHorizontal();

        // 显示最近导入的图片信息
        if (!string.IsNullOrEmpty(lastImportedImageName))
        {
            EditorGUILayout.HelpBox($"最近导入的图片: {lastImportedImageName}", MessageType.Info);
        }

        // 显示图片导入目录
        EditorGUILayout.HelpBox($"图片导入目录: {imageImportFolder}", MessageType.None);
    }
    private void DrawPrefabManagementSection()
    {
        EditorGUILayout.LabelField("预制体管理", EditorStyles.boldLabel);

        EditorGUILayout.LabelField($"当前预制体数量: {prefabList.Count}");

        // 添加预制体功能
        EditorGUILayout.LabelField("添加预制体:");
        EditorGUILayout.BeginHorizontal();
        prefabSearchName = EditorGUILayout.TextField("预制体名称", prefabSearchName);
        if (GUILayout.Button("搜索添加", GUILayout.Width(80)))
        {
            AddPrefabByName();
        }
        EditorGUILayout.EndHorizontal();

        // 显示分类后的预制体
        DrawCategorizedPrefabs();

        // 操作按钮
        EditorGUILayout.BeginHorizontal();
        if (GUILayout.Button("更新预制体索引"))
        {
            UpdatePrefabIndex();
        }

        if (GUILayout.Button("清空列表"))
        {
            ClearPrefabList();
        }

        if (GUILayout.Button("手动保存", GUILayout.Width(80)))
        {
            SavePrefabData();
            EditorUtility.DisplayDialog("成功", "预制体数据已保存", "确定");
        }
        EditorGUILayout.EndHorizontal();

        // 显示状态信息
        EditorGUILayout.HelpBox($"预制体索引数量: {prefabIndex.Count}", MessageType.Info);
    }

    private void DrawCategorizedPrefabs()
    {
        var categorizedPrefabs = CategorizePrefabsByPath();

        foreach (var category in categorizedPrefabs)
        {
            string categoryName = GetFolderNameFromPath(category.Key);
            List<PrefabData> prefabsInCategory = category.Value;

            // 初始化折叠状态
            if (!categoryFoldoutStates.ContainsKey(categoryName))
            {
                categoryFoldoutStates[categoryName] = true;
            }

            // 显示分类折叠面板
            categoryFoldoutStates[categoryName] = EditorGUILayout.Foldout(
                categoryFoldoutStates[categoryName],
                $"{categoryName} ({prefabsInCategory.Count}个预制体)"
            );

            if (categoryFoldoutStates[categoryName])
            {
                EditorGUI.indentLevel++;

                foreach (var prefabData in prefabsInCategory)
                {
                    EditorGUILayout.BeginHorizontal();

                    // 显示预制体名称
                    EditorGUILayout.LabelField(prefabData.name, GUILayout.Width(200));

                    // 打开预制体按钮
                    if (GUILayout.Button("打开", GUILayout.Width(50)))
                    {
                        OpenPrefabByName(prefabData.name);
                    }

                    // 定位预制体文件按钮
                    if (GUILayout.Button("定位", GUILayout.Width(50)))
                    {
                        LocatePrefabFile(prefabData.name);
                    }

                    // 删除按钮
                    if (GUILayout.Button("删除", GUILayout.Width(50)))
                    {
                        RemovePrefabFromListByName(prefabData.name);
                        break;
                    }

                    EditorGUILayout.EndHorizontal();
                }

                EditorGUI.indentLevel--;
            }
        }
    }

    // ========== 预制体索引相关方法 ==========
    private void LoadPrefabIndex()
    {
        try
        {
            string recordsDir = Path.GetDirectoryName(prefabIndexPath);
            if (!Directory.Exists(recordsDir))
            {
                Directory.CreateDirectory(recordsDir);
            }

            if (File.Exists(prefabIndexPath))
            {
                string json = File.ReadAllText(prefabIndexPath);
                PrefabIndexWrapper wrapper = JsonUtility.FromJson<PrefabIndexWrapper>(json);
                if (wrapper != null && wrapper.prefabIndex != null)
                {
                    prefabIndex.Clear();
                    foreach (var item in wrapper.prefabIndex)
                    {
                        if (!prefabIndex.ContainsKey(item.name))
                        {
                            prefabIndex.Add(item.name, item.path);
                        }
                    }
                    UnityEngine.Debug.Log($"预制体索引加载成功，共 {prefabIndex.Count} 个预制体");
                }
            }
            else
            {
                UnityEngine.Debug.Log("未找到预制体索引文件，将创建新索引");
                UpdatePrefabIndex();
            }
        }
        catch (Exception e)
        {
            UnityEngine.Debug.LogError($"加载预制体索引失败: {e.Message}");
        }
    }

    private void SavePrefabIndex()
    {
        try
        {
            List<PrefabIndexItem> indexList = new List<PrefabIndexItem>();
            foreach (var kvp in prefabIndex)
            {
                indexList.Add(new PrefabIndexItem { name = kvp.Key, path = kvp.Value });
            }

            PrefabIndexWrapper wrapper = new PrefabIndexWrapper
            {
                prefabIndex = indexList,
                lastUpdateTime = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")
            };

            string json = JsonUtility.ToJson(wrapper, true);

            string recordsDir = Path.GetDirectoryName(prefabIndexPath);
            if (!Directory.Exists(recordsDir))
            {
                Directory.CreateDirectory(recordsDir);
            }

            File.WriteAllText(prefabIndexPath, json);
            UnityEngine.Debug.Log($"预制体索引已保存，共 {prefabIndex.Count} 个预制体");
        }
        catch (Exception e)
        {
            UnityEngine.Debug.LogError($"保存预制体索引失败: {e.Message}");
        }
    }

    private void UpdatePrefabIndex()
    {
        try
        {
            // 将相对路径转换为绝对路径
            string searchPath = Path.Combine(Application.dataPath, "..", prefabSearchRelativePath);
            searchPath = Path.GetFullPath(searchPath);

            if (!Directory.Exists(searchPath))
            {
                EditorUtility.DisplayDialog("错误", $"搜索路径不存在: {searchPath}", "确定");
                return;
            }

            prefabIndex.Clear();

            string[] prefabFiles = Directory.GetFiles(searchPath, "*.prefab", SearchOption.AllDirectories);

            foreach (string filePath in prefabFiles)
            {
                // 将绝对路径转换为相对于项目根目录的路径
                string relativePath = GetRelativePath(filePath);
                string fileName = Path.GetFileNameWithoutExtension(filePath);

                if (!prefabIndex.ContainsKey(fileName))
                {
                    prefabIndex.Add(fileName, relativePath);
                }
            }

            SavePrefabIndex();
            EditorUtility.DisplayDialog("成功", $"预制体索引更新完成，共找到 {prefabFiles.Length} 个预制体", "确定");
        }
        catch (Exception e)
        {
            UnityEngine.Debug.LogError($"更新预制体索引失败: {e.Message}");
            EditorUtility.DisplayDialog("错误", $"更新预制体索引失败: {e.Message}", "确定");
        }
    }

    // 获取相对于项目根目录的路径
    private string GetRelativePath(string absolutePath)
    {
        string projectRoot = Path.GetFullPath(Path.Combine(Application.dataPath, ".."));
        Uri projectUri = new Uri(projectRoot + Path.DirectorySeparatorChar);
        Uri fileUri = new Uri(absolutePath);
        Uri relativeUri = projectUri.MakeRelativeUri(fileUri);
        return Uri.UnescapeDataString(relativeUri.ToString()).Replace('/', Path.DirectorySeparatorChar);
    }

    private void AddPrefabByName()
    {
        if (string.IsNullOrEmpty(prefabSearchName))
        {
            EditorUtility.DisplayDialog("提示", "请输入预制体名称", "确定");
            return;
        }

        if (prefabIndex.ContainsKey(prefabSearchName))
        {
            string prefabPath = prefabIndex[prefabSearchName];

            if (prefabList.Contains(prefabSearchName))
            {
                EditorUtility.DisplayDialog("提示", $"预制体 {prefabSearchName} 已存在列表中", "确定");
                return;
            }

            prefabList.Add(prefabSearchName);
            UpdatePrefabData(prefabSearchName, prefabPath);
            prefabSearchName = "";

            UnityEngine.Debug.Log($"已添加预制体: {prefabSearchName} ({prefabPath})");
            EditorUtility.DisplayDialog("成功", $"已添加预制体: {prefabSearchName}", "确定");
        }
        else
        {
            EditorUtility.DisplayDialog("未找到", $"未找到名为 {prefabSearchName} 的预制体\n\n请检查名称是否正确，或点击\"更新预制体索引\"按钮重新生成索引", "确定");
        }
    }

    // ========== 预制体操作相关方法 ==========
    private void OpenPrefabByName(string prefabName)
    {
        if (string.IsNullOrEmpty(prefabName))
        {
            EditorUtility.DisplayDialog("错误", "预制体名称不能为空", "确定");
            return;
        }

        string prefabPath = FindPrefabPathFromSavedData(prefabName);
        if (!string.IsNullOrEmpty(prefabPath))
        {
            OpenPrefab(prefabPath);
            return;
        }

        string[] guids = AssetDatabase.FindAssets(prefabName + " t:Prefab");
        if (guids.Length > 0)
        {
            string path = AssetDatabase.GUIDToAssetPath(guids[0]);
            OpenPrefab(path);
            UpdatePrefabPathInSavedData(prefabName, path);
        }
        else
        {
            EditorUtility.DisplayDialog("错误", $"找不到名为 {prefabName} 的预制体", "确定");
        }
    }

    private void OpenPrefab(string path)
    {
        if (string.IsNullOrEmpty(path))
        {
            EditorUtility.DisplayDialog("错误", "预制体路径不能为空", "确定");
            return;
        }

        GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(path);
        if (prefab != null)
        {
            AssetDatabase.OpenAsset(prefab);
            UnityEngine.Debug.Log($"已打开预制体进行编辑: {path}");
        }
        else
        {
            EditorUtility.DisplayDialog("错误", $"无法找到预制体: {path}", "确定");
        }
    }

    private void LocatePrefabFile(string prefabName)
    {
        if (string.IsNullOrEmpty(prefabName))
        {
            EditorUtility.DisplayDialog("错误", "预制体名称不能为空", "确定");
            return;
        }

        string prefabPath = FindPrefabPathFromSavedData(prefabName);
        if (!string.IsNullOrEmpty(prefabPath))
        {
            LocatePrefabInProject(prefabPath);
            return;
        }

        string[] guids = AssetDatabase.FindAssets(prefabName + " t:Prefab");
        if (guids.Length > 0)
        {
            string path = AssetDatabase.GUIDToAssetPath(guids[0]);
            LocatePrefabInProject(path);
            UpdatePrefabPathInSavedData(prefabName, path);
        }
        else
        {
            EditorUtility.DisplayDialog("错误", $"找不到名为 {prefabName} 的预制体", "确定");
        }
    }

    private void LocatePrefabInProject(string path)
    {
        if (string.IsNullOrEmpty(path))
        {
            EditorUtility.DisplayDialog("错误", "预制体路径不能为空", "确定");
            return;
        }

        UnityEngine.Object prefab = AssetDatabase.LoadAssetAtPath<UnityEngine.Object>(path);
        if (prefab != null)
        {
            Selection.activeObject = prefab;
            EditorGUIUtility.PingObject(prefab);
            UnityEngine.Debug.Log($"已定位到预制体: {path}");
        }
        else
        {
            EditorUtility.DisplayDialog("错误", $"无法找到预制体: {path}", "确定");
        }
    }

    // ========== 数据管理相关方法 ==========
    private void LoadPrefabData()
    {
        try
        {
            string recordsDir = Path.GetDirectoryName(prefabDataPath);
            if (!Directory.Exists(recordsDir))
            {
                Directory.CreateDirectory(recordsDir);
            }

            if (File.Exists(prefabDataPath))
            {
                string json = File.ReadAllText(prefabDataPath);
                PrefabDataWrapper wrapper = JsonUtility.FromJson<PrefabDataWrapper>(json);
                if (wrapper != null && wrapper.prefabData != null)
                {
                    savedPrefabData = wrapper.prefabData;
                    UnityEngine.Debug.Log($"成功加载 {savedPrefabData.Count} 个预制体数据");
                }
            }
        }
        catch (Exception e)
        {
            UnityEngine.Debug.LogError($"加载预制体数据失败: {e.Message}");
        }
    }

    private void SavePrefabData()
    {
        try
        {
            SyncSavedDataFromPrefabList();

            PrefabDataWrapper wrapper = new PrefabDataWrapper
            {
                prefabData = savedPrefabData,
                lastUpdateTime = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")
            };

            string json = JsonUtility.ToJson(wrapper, true);

            string recordsDir = Path.GetDirectoryName(prefabDataPath);
            if (!Directory.Exists(recordsDir))
            {
                Directory.CreateDirectory(recordsDir);
            }

            File.WriteAllText(prefabDataPath, json);
            UnityEngine.Debug.Log($"预制体数据已保存，共 {savedPrefabData.Count} 个预制体");
        }
        catch (Exception e)
        {
            UnityEngine.Debug.LogError($"保存预制体数据失败: {e.Message}");
        }
    }

    private void SyncSavedDataFromPrefabList()
    {
        savedPrefabData.RemoveAll(data => !prefabList.Contains(data.name));

        foreach (string prefabName in prefabList)
        {
            if (!string.IsNullOrEmpty(prefabName) && !savedPrefabData.Exists(data => data.name == prefabName))
            {
                savedPrefabData.Add(new PrefabData
                {
                    name = prefabName,
                    path = FindPrefabPathInProject(prefabName)
                });
            }
        }
    }

    private void SyncPrefabListFromSavedData()
    {
        prefabList.Clear();
        foreach (var data in savedPrefabData)
        {
            if (!string.IsNullOrEmpty(data.name))
            {
                prefabList.Add(data.name);
            }
        }
        UnityEngine.Debug.Log($"从保存数据中恢复了 {prefabList.Count} 个预制体");
    }

    private void UpdatePrefabData(string prefabName, string prefabPath)
    {
        var existingData = savedPrefabData.Find(data => data.name == prefabName);
        if (existingData != null)
        {
            existingData.path = prefabPath;
        }
        else
        {
            savedPrefabData.Add(new PrefabData
            {
                name = prefabName,
                path = prefabPath
            });
        }
        SavePrefabData();
    }

    private void RemovePrefabFromSavedData(string prefabName)
    {
        savedPrefabData.RemoveAll(data => data.name == prefabName);
        SavePrefabData();
    }

    private string FindPrefabPathFromSavedData(string prefabName)
    {
        var data = savedPrefabData.Find(d => d.name == prefabName);
        return data?.path;
    }

    private void UpdatePrefabPathInSavedData(string prefabName, string path)
    {
        var data = savedPrefabData.Find(d => d.name == prefabName);
        if (data != null)
        {
            data.path = path;
            SavePrefabData();
        }
    }

    private string FindPrefabPathInProject(string prefabName)
    {
        string[] guids = AssetDatabase.FindAssets(prefabName + " t:Prefab");
        if (guids.Length > 0)
        {
            return AssetDatabase.GUIDToAssetPath(guids[0]);
        }
        return "";
    }

    private void RemovePrefabFromListByName(string prefabName)
    {
        int index = prefabList.IndexOf(prefabName);
        if (index >= 0)
        {
            prefabList.RemoveAt(index);
            RemovePrefabFromSavedData(prefabName);
        }
    }

    private void ClearPrefabList()
    {
        if (prefabList.Count > 0)
        {
            if (EditorUtility.DisplayDialog("确认清空", "确定要清空所有预制体吗？", "确定", "取消"))
            {
                prefabList.Clear();
                savedPrefabData.Clear();
                SavePrefabData();
            }
        }
    }

    // ========== 工具方法 ==========
    private Dictionary<string, List<PrefabData>> CategorizePrefabsByPath()
    {
        Dictionary<string, List<PrefabData>> categorized = new Dictionary<string, List<PrefabData>>();

        foreach (var prefabData in savedPrefabData)
        {
            if (string.IsNullOrEmpty(prefabData.path))
                continue;

            string directory = Path.GetDirectoryName(prefabData.path);
            if (string.IsNullOrEmpty(directory))
            {
                directory = "未分类";
            }

            if (!categorized.ContainsKey(directory))
            {
                categorized[directory] = new List<PrefabData>();
            }

            categorized[directory].Add(prefabData);
        }

        return categorized;
    }

    private string GetFolderNameFromPath(string path)
    {
        if (string.IsNullOrEmpty(path))
            return "未分类";

        string folderName = Path.GetFileName(path);
        if (string.IsNullOrEmpty(folderName))
        {
            path = path.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
            folderName = Path.GetFileName(path);
        }

        return string.IsNullOrEmpty(folderName) ? "未分类" : folderName;
    }

    // ==================== 预览UI预制体相关方法 ====================
    private void PreviewSelectedPrefab()
    {
        try
        {
            // 检查是否在播放模式
            if (!Application.isPlaying)
            {
                bool enterPlayMode = EditorUtility.DisplayDialog(
                    "提示",
                    "预览功能需要在播放模式下运行。是否进入播放模式？",
                    "是",
                    "否"
                );

                if (enterPlayMode)
                {
                    EditorApplication.isPlaying = true;
                    // 延迟执行预览
                    EditorApplication.delayCall += () =>
                    {
                        if (Application.isPlaying)
                        {
                            ExecutePreview();
                        }
                    };
                }
                return;
            }

            ExecutePreview();
        }
        catch (Exception e)
        {
            EditorUtility.DisplayDialog("错误", $"预览失败：{e.Message}", "确定");
            Debug.LogError($"预览UI预制体失败：{e}");
        }
    }

    private void ExecutePreview()
    {
        // 获取选中的预制体
        GameObject selectedPrefab = Selection.activeObject as GameObject;

        if (selectedPrefab == null)
        {
            EditorUtility.DisplayDialog("提示", "请在Project窗口选择一个UI预制体", "确定");
            return;
        }

        // 检查是否是预制体
        if (PrefabUtility.GetPrefabAssetType(selectedPrefab) == PrefabAssetType.NotAPrefab)
        {
            EditorUtility.DisplayDialog("提示", "请选择有效的预制体文件", "确定");
            return;
        }

        // 关闭之前的预览
        ClosePreview();

        // 查找Canvas
        Transform parentTransform = null;

        if (autoFindCanvas)
        {
            // 自动查找场景中的Canvas
            Canvas canvas = FindObjectOfType<Canvas>();
            if (canvas != null)
            {
                parentTransform = canvas.transform;
                Debug.Log($"找到Canvas: {canvas.name}");
            }
            else
            {
                // 如果没有Canvas，创建一个
                GameObject canvasObj = new GameObject("PreviewCanvas");
                Canvas newCanvas = canvasObj.AddComponent<Canvas>();
                newCanvas.renderMode = RenderMode.ScreenSpaceOverlay;
                canvasObj.AddComponent<CanvasScaler>();
                canvasObj.AddComponent<GraphicRaycaster>();
                parentTransform = newCanvas.transform;
                Debug.Log("创建新的Canvas用于预览");
            }
        }
        else if (customParent != null)
        {
            parentTransform = customParent;
        }

        if (parentTransform == null)
        {
            EditorUtility.DisplayDialog("错误", "无法找到或创建父节点", "确定");
            return;
        }

        // 实例化预制体
        previewInstance = Instantiate(selectedPrefab, parentTransform);
        previewInstance.name = $"{selectedPrefab.name}_Preview";

        // 设置位置和大小
        RectTransform rectTransform = previewInstance.GetComponent<RectTransform>();
        if (rectTransform != null)
        {
            rectTransform.anchoredPosition = Vector2.zero;
            rectTransform.localScale = Vector3.one;
            rectTransform.anchorMin = new Vector2(0.5f, 0.5f);
            rectTransform.anchorMax = new Vector2(0.5f, 0.5f);
            rectTransform.pivot = new Vector2(0.5f, 0.5f);
        }

        // 添加到最上层
        previewInstance.transform.SetAsLastSibling();

        Debug.Log($"成功预览预制体: {selectedPrefab.name}");
        EditorUtility.DisplayDialog("成功",
            $"已预览预制体: {selectedPrefab.name}\n\n" +
            "操作说明：\n" +
            "1. 预览对象在场景中显示\n" +
            "2. 点击工具窗口的'关闭预览'按钮关闭预览",
            "确定");

        // 选中预览实例，方便查看
        Selection.activeGameObject = previewInstance;
    }

    private void ClosePreview()
    {
        if (previewInstance != null)
        {
            DestroyImmediate(previewInstance);
            previewInstance = null;
            Debug.Log("已关闭预览");

            // 清理可能创建的临时Canvas
            CleanupTempCanvas();
        }
    }

    private void CleanupTempCanvas()
    {
        Canvas tempCanvas = GameObject.Find("PreviewCanvas")?.GetComponent<Canvas>();
        if (tempCanvas != null && tempCanvas.transform.childCount == 0)
        {
            DestroyImmediate(tempCanvas.gameObject);
            Debug.Log("已清理临时Canvas");
        }
    }

    // ==================== 图片导入相关方法 ====================
private void ImportImageAndCreateUI()
{
    try
    {
        // 1. 选择图片文件，使用网络路径作为默认路径
        string imagePath = EditorUtility.OpenFilePanel("选择图片", defaultImportPath, "png,jpg,jpeg,tga,bmp");
        if (string.IsNullOrEmpty(imagePath))
            return;

        // 2. 确保UIImage文件夹存在
        string fullImageFolderPath = Path.Combine(Application.dataPath, "WorkRecords", "UIImage");
        if (!Directory.Exists(fullImageFolderPath))
        {
            Directory.CreateDirectory(fullImageFolderPath);
            Debug.Log($"创建UIImage文件夹: {fullImageFolderPath}");
        }

        // 3. 复制图片到UIImage文件夹
        string fileName = Path.GetFileName(imagePath);
        string destPath = Path.Combine(fullImageFolderPath, fileName);

        // 如果目标文件已存在，询问是否覆盖
        if (File.Exists(destPath))
        {
            if (!EditorUtility.DisplayDialog("文件已存在", $"文件 {fileName} 已存在，是否覆盖？", "是", "否"))
                return;
        }

        File.Copy(imagePath, destPath, true);

        // 4. 刷新AssetDatabase
        AssetDatabase.Refresh();

        // 5. 获取导入的纹理并设置TextureType
        string assetPath = Path.Combine(imageImportFolder, fileName).Replace("\\", "/");
        TextureImporter textureImporter = AssetImporter.GetAtPath(assetPath) as TextureImporter;
        if (textureImporter != null)
        {
            textureImporter.textureType = TextureImporterType.Sprite;
            textureImporter.spriteImportMode = SpriteImportMode.Single;
            textureImporter.mipmapEnabled = false;
            
            // 如果需要保留原始尺寸，可以设置Max Size
            textureImporter.maxTextureSize = 4096; // 根据实际需求调整
            textureImporter.SaveAndReimport();
        }

        // 6. 加载Sprite并获取原始尺寸
        Sprite sprite = AssetDatabase.LoadAssetAtPath<Sprite>(assetPath);
        if (sprite == null)
        {
            EditorUtility.DisplayDialog("错误", "加载Sprite失败！", "确定");
            return;
        }

        // 获取Sprite的原始像素尺寸
        float spriteWidth = sprite.rect.width;
        float spriteHeight = sprite.rect.height;
        Debug.Log($"Sprite原始尺寸: {spriteWidth} x {spriteHeight}");

        // 7. 检查当前是否有打开的Prefab
        GameObject currentPrefab = Selection.activeGameObject;
        if (currentPrefab == null)
        {
            EditorUtility.DisplayDialog("提示", "请先选择一个Prefab进行编辑", "确定");
            return;
        }

        // 8. 在Prefab根节点下创建Image对象
        string imageName = Path.GetFileNameWithoutExtension(fileName) + "_Image";
        GameObject imageObject = new GameObject(imageName);
        Image imageComponent = imageObject.AddComponent<Image>();

        // 9. 设置RectTransform使用原图尺寸和指定的pivot、anchors
        RectTransform rectTransform = imageObject.GetComponent<RectTransform>();
        
        // 设置pivot为 (0, 0.5)
        rectTransform.pivot = new Vector2(0, 0.5f);
        
        // 设置anchors为 (0, 0.5)
        rectTransform.anchorMin = new Vector2(0, 0.5f);
        rectTransform.anchorMax = new Vector2(0, 0.5f);
        
        // 设置位置为 (0, 0, 0)
        rectTransform.anchoredPosition3D = Vector3.zero;
        
        // 设置本地旋转为0
        rectTransform.localRotation = Quaternion.identity;
        
        // 设置本地缩放为1
        rectTransform.localScale = Vector3.one;
        
        // 设置尺寸为Sprite的原始尺寸
        rectTransform.sizeDelta = new Vector2(spriteWidth, spriteHeight);

        // 10. 添加LayoutElement组件（可选）
        LayoutElement layoutElement = imageObject.AddComponent<LayoutElement>();
        layoutElement.ignoreLayout = true; // 忽略自动布局，使用我们手动设置的尺寸

        // 11. 设置Sprite和颜色
        imageComponent.sprite = sprite;
        Color imageColor = imageComponent.color;
        imageColor.a = 100f / 255f; // 将100转换为0-1范围的alpha值
        imageComponent.color = imageColor;

        // 12. 将Image对象设置为Prefab的子对象
        imageObject.transform.SetParent(currentPrefab.transform, false);

        // 13. 检查父对象是否有Canvas组件，如果没有则创建一个
        Canvas parentCanvas = currentPrefab.GetComponentInParent<Canvas>();
        if (parentCanvas == null)
        {
            // 确保当前选中的对象有Canvas组件
            if (currentPrefab.GetComponent<Canvas>() == null)
            {
                Canvas canvas = currentPrefab.AddComponent<Canvas>();
                CanvasScaler scaler = currentPrefab.AddComponent<CanvasScaler>();
                GraphicRaycaster raycaster = currentPrefab.AddComponent<GraphicRaycaster>();
                
                // 设置Canvas属性
                canvas.renderMode = RenderMode.ScreenSpaceOverlay;
                
                // 设置CanvasScaler
                scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
                scaler.referenceResolution = new Vector2(1920, 1080);
                scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
                scaler.matchWidthOrHeight = 0.5f;
            }
        }

        // 14. 记录导入的图片信息
        lastImportedImagePath = assetPath;
        lastImportedImageName = fileName;

        // 15. 标记Prefab为脏以保存更改
        EditorUtility.SetDirty(currentPrefab);
        PrefabUtility.RecordPrefabInstancePropertyModifications(currentPrefab);

        Debug.Log($"成功创建Image: {imageObject.name}, 尺寸: {spriteWidth}x{spriteHeight}, Pivot: (0,0.5), Anchors: (0,0.5), 位置: (0,0,0)");
        EditorUtility.DisplayDialog("成功", 
            $"图片导入并UI创建完成！\n" +
            $"尺寸: {spriteWidth} x {spriteHeight}\n" +
            $"Pivot: (0, 0.5)\n" +
            $"Anchors: (0, 0.5)\n" +
            $"位置: (0, 0, 0)", 
            "确定");
    }
    catch (Exception e)
    {
        EditorUtility.DisplayDialog("错误", $"操作失败：{e.Message}", "确定");
        Debug.LogError($"导入图片并创建UI失败：{e}");
    }
}
    private void DeleteUIImageFolderAndObject()
    {
        try
        {
            // 1. 检查是否有记录的图片路径
            if (string.IsNullOrEmpty(lastImportedImagePath))
            {
                EditorUtility.DisplayDialog("提示", "没有找到要删除的图片记录", "确定");
                return;
            }

            // 2. 确认删除
            if (!EditorUtility.DisplayDialog("确认删除",
                $"确定要删除整个UIImage文件夹和图片 '{lastImportedImageName}' 及其对应的UI Image对象吗？", "是", "否"))
            {
                return;
            }

            // 3. 检查当前是否有打开的Prefab
            GameObject currentPrefab = Selection.activeGameObject;
            if (currentPrefab == null)
            {
                EditorUtility.DisplayDialog("错误", "请先选择包含Image对象的Prefab", "确定");
                return;
            }

            // 4. 查找并删除Image对象
            Transform imageTransform = currentPrefab.transform.Find("BackgroundImage");
            if (imageTransform != null)
            {
                DestroyImmediate(imageTransform.gameObject);
                EditorUtility.SetDirty(currentPrefab);
                PrefabUtility.RecordPrefabInstancePropertyModifications(currentPrefab);
                Debug.Log("已删除BackgroundImage对象");
            }
            else
            {
                Debug.LogWarning("未找到BackgroundImage对象，可能已被手动删除");
            }

            // 5. 删除整个UIImage文件夹
            if (Directory.Exists(Path.Combine(Application.dataPath, "WorkRecords", "UIImage")))
            {
                // 使用AssetDatabase删除整个文件夹
                if (AssetDatabase.DeleteAsset(imageImportFolder))
                {
                    Debug.Log($"已删除UIImage文件夹: {imageImportFolder}");
                }
                else
                {
                    Debug.LogWarning($"无法通过AssetDatabase删除文件夹: {imageImportFolder}");
                    // 尝试直接删除文件夹
                    try
                    {
                        Directory.Delete(Path.Combine(Application.dataPath, "WorkRecords", "UIImage"), true);
                        // 删除meta文件
                        string metaFilePath = Path.Combine(Application.dataPath, "WorkRecords", "UIImage.meta");
                        if (File.Exists(metaFilePath))
                        {
                            File.Delete(metaFilePath);
                        }
                        Debug.Log("已直接删除UIImage文件夹");
                    }
                    catch (Exception ex)
                    {
                        Debug.LogError($"删除文件夹失败: {ex.Message}");
                    }
                }
            }
            else
            {
                Debug.LogWarning($"UIImage文件夹不存在: {imageImportFolder}");
            }

            // 6. 刷新AssetDatabase
            AssetDatabase.Refresh();

            // 7. 清空记录
            lastImportedImagePath = "";
            lastImportedImageName = "";

            EditorUtility.DisplayDialog("成功", "已删除UIImage文件夹和Image对象", "确定");
        }
        catch (Exception e)
        {
            EditorUtility.DisplayDialog("错误", $"删除失败：{e.Message}", "确定");
            Debug.LogError($"删除UIImage文件夹和对象失败：{e}");
        }
    }

    private void OnDestroy()
    {
        // 关闭窗口时清理预览
        ClosePreview();
    }

    // ========== 数据类定义 ==========
    [System.Serializable]
    private class PrefabData
    {
        public string name;
        public string path;
    }

    [System.Serializable]
    private class PrefabDataWrapper
    {
        public List<PrefabData> prefabData;
        public string lastUpdateTime;
    }

    [System.Serializable]
    private class PrefabIndexItem
    {
        public string name;
        public string path;
    }

    [System.Serializable]
    private class PrefabIndexWrapper
    {
        public List<PrefabIndexItem> prefabIndex;
        public string lastUpdateTime;
    }
}