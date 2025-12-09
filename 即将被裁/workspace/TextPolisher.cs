using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using UnityEditor;
using UnityEngine;

// Person类定义
[System.Serializable]
public class Person
{
    public string name;
    public string gender;
    public string position;
    public string department;
    public string region;
    public DateTime joinDate;

    public Person(string name, string gender, string position, string department, string region = "青岛", DateTime joinDate = default)
    {
        this.name = name;
        this.gender = gender;
        this.position = position;
        this.department = department;
        this.region = region;
        this.joinDate = joinDate;
    }

    public string GetDescription()
    {
        return $"{position}：{name}({gender})";
    }

    public string GetDetailedInfo()
    {
        return $"姓名：{name}，性别：{gender}，部门：{department}，职务：{position}，地域：{region}";
    }
}

public class TextPolisher : EditorWindow
{
    private string inputText = "";
    private string outputText = "";
    private string apiKey = "sk-b4468b3ac8354ede9b0e12ee67a528a3";
    private bool isProcessing = false;
    private Vector2 scrollPosition;
    private string newExample = "";

    // 发送对象相关
    private Dictionary<string, List<Person>> departmentMembers = new Dictionary<string, List<Person>>();
    private Dictionary<string, bool[]> selectedMembers = new Dictionary<string, bool[]>();

    // 参考示例范围选择
    private int selectedExampleRange = 0;
    private string[] exampleRanges = { "个人示例", "部门示例", "所有示例" };

    // 分类示例存储
    private ExampleData exampleData;
    private string examplesFilePath;

    // 折叠面板状态
    private bool showRecipientSelection = true;
    private bool showExampleSettings = false;
    private bool showExampleInput = false;
    
    // 搜索功能
    private string searchName = "";
    private List<Person> searchResults = new List<Person>();

    private void OnEnable()
    {
        examplesFilePath = Path.Combine(Application.dataPath, "WorkRecords/TextPolisherExamples.json");
        InitializeDepartmentMembers();
        LoadExamples();
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


    private void InitializeDepartmentMembers()
    {
        // 初始化各部门成员
        departmentMembers["美术"] = new List<Person>
        {
            new Person("左长生", "男", "主美（队长）", "美术", "青岛", new DateTime(2010, 8, 4)),
            new Person("周雪峰", "男", "UI搭建工程师", "美术", "上海", new DateTime(2025, 11, 20)),
            new Person("邵长青", "男", "UI搭建工程师", "美术", "青岛", new DateTime(2024, 6, 24)),
            new Person("赵贵阳", "未知", "UI动效设计师", "美术", "上海", new DateTime(2022, 1, 5)),
            new Person("肖湘子", "未知", "UI设计师", "美术", "上海", new DateTime(2024, 12, 24)),
            new Person("郑嘉明", "男", "UI设计师", "美术", "广州", new DateTime(2025, 11, 25)),
            new Person("郭海舟", "未知", "特效设计师", "美术", "上海", new DateTime(2025, 11, 25)),
            new Person("宋文婷", "女", "UI设计师", "美术", "上海", new DateTime(2021, 4, 1)),
            new Person("韩红菱", "未知", "UI设计师", "美术", "青岛", new DateTime(2021, 4, 12)),
        };

        departmentMembers["测试"] = new List<Person>
        {
            new Person("师刚", "男", "测试工程师", "测试", "青岛", new DateTime(2024, 12, 23))
        };

        departmentMembers["策划"] = new List<Person>
        {
            new Person("张益豪", "男", "探索策划（队长）", "策划", "青岛", new DateTime(2024, 4, 8)),
            new Person("程菡鑫", "男", "系统策划（队长）", "策划", "青岛", new DateTime(2010, 7, 14)),
            new Person("张扬", "男", "系统策划", "策划", "青岛", new DateTime(2025, 1, 13)),
            new Person("周俊玮", "男", "系统策划", "策划", "上海", new DateTime(2024, 11, 11)),
            new Person("王诗航", "女", "系统策划", "策划", "上海", new DateTime(2025, 6, 10)),
            new Person("郭科举", "男", "系统策划", "策划", "上海", new DateTime(2025, 11, 5)),
            new Person("孙国钦", "男", "关卡策划", "策划", "青岛", new DateTime(2025, 1, 13)),
            new Person("李佳新", "男", "运营策划", "策划", "上海", new DateTime(2025, 11, 20)),
            new Person("衣光辉", "男", "系统策划组长（队长）", "策划", "青岛", new DateTime(2019, 1, 2)),
            new Person("陈其越", "未知", "系统策划", "策划", "上海", new DateTime(2025, 11, 20)),
        };

        departmentMembers["程序"] = new List<Person>
        {
            new Person("孟庆威", "男", "U3D主程（队长）", "程序", "青岛", new DateTime(2024, 5, 15)),
            new Person("许文涛", "男", "主程", "程序", "广州", new DateTime(2007, 3, 13)),
            new Person("宋传扬", "男", "U3D系统程序", "程序", "青岛", new DateTime(2019, 3, 25)),
            new Person("孙登瑞", "男", "U3D系统程序", "程序", "青岛", new DateTime(2024, 3, 25)),
            new Person("李榜鑫", "男", "U3D系统程序", "程序", "青岛", new DateTime(2024, 4, 22)),
            new Person("卢圣林", "男", "U3D优化程序", "程序", "上海", new DateTime(2024, 9, 2)),
            new Person("夏秋实", "男", "U3D优化程序", "程序", "青岛", new DateTime(2025, 11, 5)),
            new Person("卞言松", "男", "U3D战斗程序", "程序", "广州", new DateTime(2025, 11, 10)),
            new Person("谢启祥", "男", "U3D战斗程序", "程序", "广州", new DateTime(2024, 8, 6)),
            new Person("孔令召", "男", "U3D开发工程师", "程序", "上海", new DateTime(2025, 11, 30)),
            new Person("李舜丞", "男", "U3D开发工程师", "程序", "广州", new DateTime(2025, 11, 15)),
            new Person("刘军", "男", "U3D开发工程师", "程序", "青岛", new DateTime(2009, 12, 21)),
            new Person("姚则鑫", "男", "U3D开发工程师", "程序", "上海", new DateTime(2025, 11, 8))
        };

        departmentMembers["人事"] = new List<Person>
        {
            new Person("刘少峰", "男", "招聘主管", "人事", "青岛", new DateTime(2023, 7, 10))
        };

        // 初始化选择状态
        foreach (var department in departmentMembers.Keys)
        {
            selectedMembers[department] = new bool[departmentMembers[department].Count];
        }
    }

    private void OnGUI()
    {
        scrollPosition = EditorGUILayout.BeginScrollView(scrollPosition);
        
        EditorGUILayout.Space(5);
        EditorGUILayout.LabelField("文本润色工具", EditorStyles.boldLabel);
        
        // 发送对象选择折叠面板
        showRecipientSelection = EditorGUILayout.Foldout(showRecipientSelection, "发送对象选择", true);
        if (showRecipientSelection)
        {
            EditorGUILayout.BeginVertical("box");
            DrawRecipientSelection();
            EditorGUILayout.EndVertical();
        }

        EditorGUILayout.Space(5);
        
        // 示例设置折叠面板
        showExampleSettings = EditorGUILayout.Foldout(showExampleSettings, "示例设置", true);
        if (showExampleSettings)
        {
            EditorGUILayout.BeginVertical("box");
            
            EditorGUILayout.BeginHorizontal();
            EditorGUILayout.LabelField("参考范围:", GUILayout.Width(70));
            selectedExampleRange = EditorGUILayout.Popup(selectedExampleRange, exampleRanges, GUILayout.Width(100));
            EditorGUILayout.LabelField($"({GetExampleRangeCount()}条)", EditorStyles.miniLabel, GUILayout.Width(50));
            EditorGUILayout.EndHorizontal();
            
            if (GUILayout.Button("管理示例", GUILayout.Height(20)))
            {
                ShowExamplesManager();
            }
            
            EditorGUILayout.EndVertical();
        }

        EditorGUILayout.Space(5);
        
        // 示例输入折叠面板
        showExampleInput = EditorGUILayout.Foldout(showExampleInput, "添加示例", true);
        if (showExampleInput)
        {
            EditorGUILayout.BeginVertical("box");
            
            EditorGUILayout.LabelField($"添加到: {GetCurrentExampleCategory()}", EditorStyles.miniLabel);
            newExample = EditorGUILayout.TextArea(newExample, GUILayout.Height(40));
            
            if (GUILayout.Button("添加示例", GUILayout.Height(25)) && !string.IsNullOrEmpty(newExample))
            {
                if (HasSelectedRecipients())
                {
                    AddExample(newExample);
                    newExample = "";
                }
                else
                {
                    EditorUtility.DisplayDialog("提示", "请至少选择一个发送对象", "确定");
                }
            }
            
            EditorGUILayout.EndVertical();
        }

        EditorGUILayout.Space(10);
        
        // 主要功能区域
        EditorGUILayout.LabelField("输入文本:", EditorStyles.boldLabel);
        inputText = EditorGUILayout.TextArea(inputText, GUILayout.Height(80));
        
        EditorGUILayout.BeginHorizontal();
        if (GUILayout.Button("润色文本", GUILayout.Height(30)))
        {
            if (!string.IsNullOrEmpty(inputText))
            {
                if (HasSelectedRecipients())
                {
                    Polishtext();
                }
                else
                {
                    EditorUtility.DisplayDialog("提示", "请至少选择一个发送对象", "确定");
                }
            }
            else
            {
                EditorUtility.DisplayDialog("提示", "请输入要润色的文本", "确定");
            }
        }
        
        if (GUILayout.Button("清空输入", GUILayout.Height(30), GUILayout.Width(80)))
        {
            inputText = "";
            outputText = "";
        }
        EditorGUILayout.EndHorizontal();

        // 处理状态显示
        if (isProcessing)
        {
            EditorGUILayout.HelpBox("正在处理中...", MessageType.Info);
            Repaint();
        }

        EditorGUILayout.Space(5);
        
        // 输出区域
        if (!string.IsNullOrEmpty(outputText))
        {
            EditorGUILayout.LabelField("润色结果:", EditorStyles.boldLabel);
            outputText = EditorGUILayout.TextArea(outputText, GUILayout.Height(100));
            
            EditorGUILayout.BeginHorizontal();
            if (GUILayout.Button("复制结果", GUILayout.Height(25)))
            {
                GUIUtility.systemCopyBuffer = outputText;
                EditorUtility.DisplayDialog("成功", "结果已复制到剪贴板", "确定");
            }
            EditorGUILayout.EndHorizontal();
        }

        // 显示发送对象信息
        DisplaySelectedRecipients();
        
        EditorGUILayout.EndScrollView();
    }

    private void DrawRecipientSelection()
    {
        // 搜索框
        EditorGUILayout.BeginHorizontal();
        EditorGUILayout.LabelField("搜索:", GUILayout.Width(40));
        
        // 输入搜索词时实时搜索
        string previousSearch = searchName;
        searchName = EditorGUILayout.TextField(searchName);
        
        // 如果搜索词发生变化，重新搜索
        if (searchName != previousSearch && !string.IsNullOrEmpty(searchName))
        {
            PerformSearch();
        }
        
        // 搜索按钮
        if (GUILayout.Button("搜索", GUILayout.Width(50)))
        {
            PerformSearch();
        }
        
        // 清空搜索按钮
        if (GUILayout.Button("清空", GUILayout.Width(50)))
        {
            searchName = "";
            searchResults.Clear();
        }
        EditorGUILayout.EndHorizontal();
        
        EditorGUILayout.Space(5);
        
        // 如果没有搜索词，显示提示
        if (string.IsNullOrEmpty(searchName))
        {
            EditorGUILayout.HelpBox("请输入姓名、职务或部门进行搜索", MessageType.Info);
            return;
        }
        
        // 显示搜索结果
        if (searchResults.Count == 0)
        {
            EditorGUILayout.HelpBox($"未找到包含 '{searchName}' 的成员", MessageType.Warning);
            return;
        }
        
        // 显示搜索结果标题
        EditorGUILayout.LabelField($"搜索结果 ({searchResults.Count}人):", EditorStyles.boldLabel);
        
        // 显示搜索结果列表
        DrawMemberGrid(searchResults);
        
        // 只保留清空已选按钮
        if (searchResults.Count > 0)
        {
            EditorGUILayout.Space(5);
            if (GUILayout.Button("清空已选", GUILayout.Height(20)))
            {
                ClearAllSelections();
            }
        }
    }
    
    private void PerformSearch()
    {
        if (string.IsNullOrEmpty(searchName))
        {
            searchResults.Clear();
            return;
        }
        
        searchResults.Clear();
        
        // 搜索关键词（不区分大小写）
        string searchKeyword = searchName.ToLower();
        
        // DEBUG: 打印搜索关键词
        Debug.Log($"搜索关键词: {searchKeyword}");
        
        // 在所有部门成员中搜索
        foreach (var department in departmentMembers.Keys)
        {
            var members = departmentMembers[department];
            
            // DEBUG: 打印每个部门的成员数量
            Debug.Log($"{department}部门有 {members.Count} 名成员");
            
            foreach (var person in members)
            {
                // 检查姓名、职务、部门是否包含搜索词（不区分大小写）
                bool match = 
                    person.name.ToLower().Contains(searchKeyword) ||
                    person.position.ToLower().Contains(searchKeyword) ||
                    person.department.ToLower().Contains(searchKeyword) ||
                    person.region.ToLower().Contains(searchKeyword);
                
                if (match)
                {
                    Debug.Log($"找到匹配: {person.name} - {person.department} - {person.position}");
                    searchResults.Add(person);
                }
            }
        }
        
        // DEBUG: 打印搜索结果数量
        Debug.Log($"找到 {searchResults.Count} 个结果");
        
        // 按入职日期排序
        searchResults = searchResults.OrderBy(p => p.joinDate).ToList();
    }
    
    private void DrawMemberGrid(List<Person> members)
    {
        int membersPerRow = 5;
        int totalRows = Mathf.CeilToInt((float)members.Count / membersPerRow);
        
        for (int row = 0; row < totalRows; row++)
        {
            EditorGUILayout.BeginHorizontal(GUILayout.ExpandWidth(false));
            for (int col = 0; col < membersPerRow; col++)
            {
                int index = row * membersPerRow + col;
                if (index < members.Count)
                {
                    var person = members[index];
                    
                    // 找到该成员在其部门中的原始索引
                    string personDept = person.department;
                    var deptMembers = departmentMembers[personDept];
                    int originalIndex = -1;
                    
                    for (int i = 0; i < deptMembers.Count; i++)
                    {
                        if (deptMembers[i].name == person.name && deptMembers[i].department == person.department)
                        {
                            originalIndex = i;
                            break;
                        }
                    }
                    
                    if (originalIndex == -1) continue;
                    
                    var selections = selectedMembers[personDept];
                    
                    EditorGUILayout.BeginVertical("box", GUILayout.Width(20), GUILayout.ExpandWidth(false), GUILayout.Height(85));
                    
                    // 选择框和姓名
                    EditorGUILayout.BeginHorizontal(GUILayout.ExpandWidth(false));
                    bool newValue = EditorGUILayout.Toggle(selections[originalIndex], GUILayout.Width(10));
                    if (newValue != selections[originalIndex])
                    {
                        selections[originalIndex] = newValue;
                    }
                    
                    // 显示姓名，已选的加粗显示
                    GUIStyle nameStyle = selections[originalIndex] ? EditorStyles.boldLabel : EditorStyles.label;
                    EditorGUILayout.LabelField(person.name, nameStyle, GUILayout.ExpandWidth(false));
                    EditorGUILayout.EndHorizontal();
                    
                    // 详细信息 - 紧凑显示所有信息
                    EditorGUILayout.LabelField($"{person.gender}|{person.position}", EditorStyles.miniLabel, GUILayout.ExpandWidth(false));
                    EditorGUILayout.LabelField($"{person.region}|{person.department}", EditorStyles.miniLabel, GUILayout.ExpandWidth(false));
                    string joinDateStr = person.joinDate != default(DateTime) ? person.joinDate.ToString("yyyy-MM-dd") : "未知";
                    EditorGUILayout.LabelField($"入职:{joinDateStr}", EditorStyles.miniLabel, GUILayout.ExpandWidth(false));
                    
                    EditorGUILayout.EndVertical();
                }
                else
                {
                    EditorGUILayout.LabelField("", GUILayout.Width(70));
                }
            }
            EditorGUILayout.EndHorizontal();
        }
    }
    
    private void ClearAllSelections()
    {
        foreach (var department in selectedMembers.Keys)
        {
            for (int i = 0; i < selectedMembers[department].Length; i++)
            {
                selectedMembers[department][i] = false;
            }
        }
    }

    private string GetExampleRangeDescription()
    {
        switch (selectedExampleRange)
        {
            case 0: return "仅使用当前选中个人的示例";
            case 1: return "使用当前选中部门所有成员的示例";
            case 2: return "使用所有部门和个人的示例";
            default: return "";
        }
    }

    private int GetExampleRangeCount()
    {
        switch (selectedExampleRange)
        {
            case 0: return GetPersonalExamples().Count;
            case 1: return GetDepartmentExamples().Count;
            case 2: return GetTotalExampleCount();
            default: return 0;
        }
    }

    private string GetCurrentExampleCategory()
    {
        // 获取所有选中的成员
        var selectedPersons = new List<Person>();
        var selectedNames = new List<string>();
        
        foreach (var department in departmentMembers.Keys)
        {
            var members = departmentMembers[department];
            var selections = selectedMembers[department];
            
            for (int i = 0; i < members.Count; i++)
            {
                if (selections[i])
                {
                    selectedPersons.Add(members[i]);
                    selectedNames.Add($"{members[i].department}-{members[i].name}");
                }
            }
        }
        
        if (selectedNames.Count == 0) return "未选择";
        if (selectedNames.Count == 1) return selectedNames[0];
        
        // 按部门分组
        var byDepartment = selectedPersons
            .GroupBy(p => p.department)
            .Select(g => $"{g.Key} ({g.Count()}人)")
            .ToList();
        
        return $"{selectedPersons.Count}人 - " + string.Join(", ", byDepartment);
    }

    private int GetCurrentExampleCount()
    {
        // 获取当前选中个人的所有示例
        var examples = new List<string>();
        
        foreach (var department in departmentMembers.Keys)
        {
            var members = departmentMembers[department];
            var selections = selectedMembers[department];
            
            for (int i = 0; i < members.Count; i++)
            {
                if (selections[i])
                {
                    string category = $"{department}-{members[i].name}";
                    var categoryData = exampleData.categories.Find(c => c.categoryName == category);
                    if (categoryData != null)
                    {
                        examples.AddRange(categoryData.examples);
                    }
                }
            }
        }
        
        return examples.Count;
    }

    private int GetTotalExampleCount()
    {
        return exampleData.categories.Sum(c => c.examples.Count);
    }

    private bool HasSelectedRecipients()
    {
        foreach (var department in departmentMembers.Keys)
        {
            if (selectedMembers[department].Any(selected => selected))
                return true;
        }
        return false;
    }

    private void DisplaySelectedRecipients()
    {
        var selectedPersons = new List<Person>();
        
        foreach (var department in departmentMembers.Keys)
        {
            var members = departmentMembers[department];
            var selections = selectedMembers[department];
            
            for (int i = 0; i < members.Count; i++)
            {
                if (selections[i])
                {
                    selectedPersons.Add(members[i]);
                }
            }
        }
        
        if (selectedPersons.Count > 0)
        {
            EditorGUILayout.Space(5);
            
            // 按部门分组统计
            var stats = selectedPersons
                .GroupBy(p => p.department)
                .Select(g => $"{g.Key}: {g.Count()}人")
                .ToArray();
            
            string statsText = $"总计: {selectedPersons.Count}人";
            if (stats.Length > 0)
            {
                statsText += $" ({string.Join(", ", stats)})";
            }
            
            EditorGUILayout.LabelField(statsText, EditorStyles.boldLabel);
            
            // 显示选中的人员列表（限制显示数量）
            int maxDisplay = 5;
            var displayList = selectedPersons.Select(p => $"{p.name}({p.department})").ToList();
            string displayText;
            
            if (displayList.Count <= maxDisplay)
            {
                displayText = string.Join("、", displayList);
            }
            else
            {
                displayText = string.Join("、", displayList.Take(maxDisplay)) + $"等{displayList.Count}人";
            }
            
            EditorGUILayout.HelpBox($"发送给: {displayText}", MessageType.Info);
        }
        else if (!string.IsNullOrEmpty(inputText) || !string.IsNullOrEmpty(outputText))
        {
            EditorGUILayout.Space(5);
            EditorGUILayout.HelpBox("请选择发送对象", MessageType.Warning);
        }
    }

    private void AddExample(string example)
    {
        // 为每个选中的个人单独添加示例
        foreach (var department in departmentMembers.Keys)
        {
            var members = departmentMembers[department];
            var selections = selectedMembers[department];
            
            for (int i = 0; i < members.Count; i++)
            {
                if (selections[i])
                {
                    string category = $"{department}-{members[i].name}";
                    var categoryData = exampleData.categories.Find(c => c.categoryName == category);
                    
                    if (categoryData == null)
                    {
                        categoryData = new CategoryData { categoryName = category, examples = new List<string>() };
                        exampleData.categories.Add(categoryData);
                    }
                    
                    if (!categoryData.examples.Contains(example))
                    {
                        categoryData.examples.Add(example);
                    }
                }
            }
        }
        
        SaveExamples();
        EditorUtility.DisplayDialog("成功", $"示例已添加到 {GetCurrentExampleCategory()}", "确定");
    }

    private void LoadExamples()
    {
        if (File.Exists(examplesFilePath))
        {
            try
            {
                string json = File.ReadAllText(examplesFilePath);
                exampleData = JsonUtility.FromJson<ExampleData>(json);
                
                if (exampleData == null || exampleData.categories == null)
                {
                    CreateDefaultExampleData();
                }
            }
            catch (System.Exception ex)
            {
                Debug.LogError($"加载示例失败: {ex}");
                CreateDefaultExampleData();
            }
        }
        else
        {
            CreateDefaultExampleData();
        }
    }

    private void CreateDefaultExampleData()
    {
        exampleData = new ExampleData { categories = new List<CategoryData>() };
    }

    private void SaveExamples()
    {
        try
        {
            string directory = Path.GetDirectoryName(examplesFilePath);
            if (!Directory.Exists(directory))
                Directory.CreateDirectory(directory);
            
            string json = JsonUtility.ToJson(exampleData, true);
            File.WriteAllText(examplesFilePath, json);
        }
        catch (System.Exception ex)
        {
            Debug.LogError($"保存示例失败: {ex}");
        }
    }

    private void ShowExamplesManager()
    {
        ExamplesManager.ShowWindow(exampleData, this);
    }

    public void UpdateExamples(ExampleData newExampleData)
    {
        exampleData = newExampleData;
        SaveExamples();
    }

    private async void Polishtext()
    {
        if (isProcessing) return;
        
        isProcessing = true;
        outputText = "";
        Repaint();
        
        try
        {
            var result = await PolishTextWithDeepSeek(inputText);
            outputText = result;
        }
        catch (System.Exception ex)
        {
            outputText = $"错误: {ex.Message}";
            Debug.LogError($"润色失败: {ex}");
        }
        finally
        {
            isProcessing = false;
            Repaint();
        }
    }

    private async Task<string> PolishTextWithDeepSeek(string text)
    {
        using (var client = new HttpClient())
        {
            client.DefaultRequestHeaders.Add("Authorization", $"Bearer {apiKey}");
            
            string examplesPrompt = BuildExamplesPrompt();
            string recipientsInfo = BuildRecipientsInfoPrompt();
            
            string cleanedInput = CleanJsonString(text);
            string cleanedExamples = CleanJsonString(examplesPrompt);
            string cleanedRecipients = CleanJsonString(recipientsInfo);
            
            string jsonRequest = $@"{{
    ""model"": ""deepseek-chat"",
    ""messages"": [
        {{
            ""role"": ""system"",
            ""content"": ""你是一个专业的文本润色助手。请根据发送对象的身份、职务和沟通习惯，模仿用户提供的示例文本的风格和语气，对输入的文本进行润色。保持原意不变，但要让表达更加自然、流畅、符合接收者的身份特点和沟通风格。直接返回润色后的文本，不要添加其他说明.""
        }},
        {{
            ""role"": ""user"",
            ""content"": ""发送对象信息：\n{cleanedRecipients}\n\n参考示例文本的风格：\n{cleanedExamples}\n\n现在请根据上述发送对象信息和参考示例风格，润色以下文本：\n'{cleanedInput}'""
        }}
    ],
    ""max_tokens"": 2000,
    ""temperature"": 0.7
}}";
            
            var content = new StringContent(jsonRequest, Encoding.UTF8, "application/json");
            var response = await client.PostAsync("https://api.deepseek.com/v1/chat/completions", content);
            var responseContent = await response.Content.ReadAsStringAsync();
            
            if (response.IsSuccessStatusCode)
            {
                return ParseApiResponse(responseContent);
            }
            else
            {
                throw new System.Exception($"API请求失败: {response.StatusCode}");
            }
        }
    }

    private string BuildRecipientsInfoPrompt()
    {
        var selectedPersons = new List<Person>();
        
        foreach (var department in departmentMembers.Keys)
        {
            var members = departmentMembers[department];
            var selections = selectedMembers[department];
            
            for (int i = 0; i < members.Count; i++)
            {
                if (selections[i])
                {
                    selectedPersons.Add(members[i]);
                }
            }
        }
        
        if (selectedPersons.Count == 0) return "无特定发送对象";
        
        string prompt = "本次消息发送给以下人员：\n";
        foreach (var person in selectedPersons)
        {
            prompt += $"- {person.GetDetailedInfo()}\n";
        }
        return prompt;
    }

    private string BuildExamplesPrompt()
    {
        var relevantExamples = selectedExampleRange switch
        {
            0 => GetPersonalExamples(),
            1 => GetDepartmentExamples(),
            2 => GetAllExamples(),
            _ => new List<string>()
        };
        
        string prompt = "";
        for (int i = 0; i < relevantExamples.Count && i < 10; i++)
        {
            prompt += $"示例 {i + 1}: {relevantExamples[i]}\n";
        }
        return prompt;
    }

    private List<string> GetPersonalExamples()
    {
        var examples = new List<string>();
        
        foreach (var department in departmentMembers.Keys)
        {
            var members = departmentMembers[department];
            var selections = selectedMembers[department];
            
            for (int i = 0; i < members.Count; i++)
            {
                if (selections[i])
                {
                    string category = $"{department}-{members[i].name}";
                    var categoryData = exampleData.categories.Find(c => c.categoryName == category);
                    if (categoryData != null)
                    {
                        examples.AddRange(categoryData.examples);
                    }
                }
            }
        }
        
        return examples;
    }

    private List<string> GetDepartmentExamples()
    {
        var examples = new List<string>();
        
        // 获取所有选中成员所属部门的示例
        var selectedDepartments = new HashSet<string>();
        foreach (var department in departmentMembers.Keys)
        {
            var selections = selectedMembers[department];
            if (selections.Any(selected => selected))
            {
                selectedDepartments.Add(department);
            }
        }
        
        foreach (var department in selectedDepartments)
        {
            examples.AddRange(exampleData.categories
                .Where(c => c.categoryName.StartsWith(department + "-"))
                .SelectMany(c => c.examples));
        }
        
        return examples;
    }

    private List<string> GetAllExamples()
    {
        return exampleData.categories.SelectMany(c => c.examples).ToList();
    }

    private string CleanJsonString(string input)
    {
        if (string.IsNullOrEmpty(input)) return input;
        
        string cleaned = Regex.Replace(input, @"[\x00-\x08\x0B\x0C\x0E-\x1F]", "");
        cleaned = cleaned.Replace("\\", "\\\\")
                        .Replace("\"", "\\\"")
                        .Replace("\n", "\\n")
                        .Replace("\r", "\\r")
                        .Replace("\t", "\\t");
        return cleaned;
    }

    private string ParseApiResponse(string jsonResponse)
    {
        try
        {
            int contentIndex = jsonResponse.IndexOf("\"content\":\"");
            if (contentIndex == -1) throw new System.Exception("无法找到content字段");
            
            contentIndex += 11;
            int contentEndIndex = jsonResponse.IndexOf("\"", contentIndex);
            if (contentEndIndex == -1) throw new System.Exception("无法找到content字段的结束位置");
            
            string content = jsonResponse.Substring(contentIndex, contentEndIndex - contentIndex);
            content = content.Replace("\\n", "\n").Replace("\\\"", "\"").Replace("\\\\", "\\");
            return content.Trim();
        }
        catch (System.Exception ex)
        {
            throw new System.Exception($"解析API响应失败: {ex.Message}");
        }
    }

    [System.Serializable]
    public class ExampleData
    {
        public List<CategoryData> categories;
    }

    [System.Serializable]
    public class CategoryData
    {
        public string categoryName;
        public List<string> examples;
    }
}

// 示例管理窗口
public class ExamplesManager : EditorWindow
{
    private TextPolisher.ExampleData exampleData;
    private TextPolisher parentWindow;
    private Vector2 scrollPosition;
    private string searchText = "";

    public static void ShowWindow(TextPolisher.ExampleData data, TextPolisher parent)
    {
        ExamplesManager window = GetWindow<ExamplesManager>("示例管理");
        window.exampleData = data;
        window.parentWindow = parent;
    }

    private void OnGUI()
    {
        GUILayout.Label("示例管理", EditorStyles.boldLabel);
        
        // 搜索框
        EditorGUILayout.BeginHorizontal();
        GUILayout.Label("搜索:", GUILayout.Width(40));
        searchText = EditorGUILayout.TextField(searchText);
        EditorGUILayout.EndHorizontal();
        
        scrollPosition = EditorGUILayout.BeginScrollView(scrollPosition);
        
        foreach (var category in exampleData.categories.ToList())
        {
            if (!string.IsNullOrEmpty(searchText) &&
                !category.categoryName.Contains(searchText) &&
                !category.examples.Any(ex => ex.Contains(searchText)))
                continue;
            
            EditorGUILayout.BeginVertical("box");
            
            EditorGUILayout.BeginHorizontal();
            EditorGUILayout.LabelField($"{category.categoryName} ({category.examples.Count}个)", EditorStyles.boldLabel);
            
            if (GUILayout.Button("删除", GUILayout.Width(60)))
            {
                if (EditorUtility.DisplayDialog("确认", $"删除分类 [{category.categoryName}]?", "确定", "取消"))
                {
                    exampleData.categories.Remove(category);
                    break;
                }
            }
            EditorGUILayout.EndHorizontal();
            
            for (int i = category.examples.Count - 1; i >= 0; i--)
            {
                if (!string.IsNullOrEmpty(searchText) && !category.examples[i].Contains(searchText))
                    continue;
                
                EditorGUILayout.BeginHorizontal();
                category.examples[i] = EditorGUILayout.TextArea(category.examples[i], GUILayout.Height(40));
                
                EditorGUILayout.BeginVertical(GUILayout.Width(80));
                if (GUILayout.Button("使用"))
                {
                    parentWindow.SetInputText(category.examples[i]);
                    Close();
                }
                if (GUILayout.Button("删除"))
                {
                    category.examples.RemoveAt(i);
                }
                EditorGUILayout.EndVertical();
                EditorGUILayout.EndHorizontal();
            }
            
            EditorGUILayout.EndVertical();
        }
        
        EditorGUILayout.EndScrollView();
        
        if (GUILayout.Button("保存并关闭", GUILayout.Height(30)))
        {
            parentWindow.UpdateExamples(exampleData);
            Close();
        }
    }
}

// 扩展方法
public static class TextPolisherExtensions
{
    public static void SetInputText(this TextPolisher polisher, string text)
    {
        var field = typeof(TextPolisher).GetField("inputText",
            System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
        if (field != null)
        {
            field.SetValue(polisher, text);
        }
    }
}