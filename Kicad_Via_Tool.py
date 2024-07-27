import pcbnew
import wx
import os

class SelectViasByNet(pcbnew.ActionPlugin):
    def __init__(self):
        self.name = "Kicad_Via_Tool"
        self.category = "Modify"
        self.description = "Select all vias of a specified net and optionally change their sizes"
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(os.path.dirname(__file__), "Kicad_Via_Tool.png")

    def Run(self):
        print("Running SelectViasByNet plugin")
        dialog = NetNameDialog(None)
        while True:
            try:
                if dialog.ShowModal() == wx.ID_OK:
                    net_name = dialog.net_name
                    use_zone = dialog.use_zone
                    min_size = dialog.min_size
                    max_size = dialog.max_size
                    action = dialog.action
                    new_drill_size = dialog.new_drill_size
                    new_diameter = dialog.new_diameter
                    zone = None
                    if use_zone:
                        zone = get_selected_zone()
                        if zone is None:
                            print("No zone selected")
                            continue
                    print(f"Running selection with parameters: net_name={net_name}, use_zone={use_zone}, min_size={min_size}, max_size={max_size}, action={action}, new_drill_size={new_drill_size}, new_diameter={new_diameter}")
                    select_vias_by_net(net_name, use_zone, zone, min_size, max_size, action, new_drill_size, new_diameter)
                else:
                    break
            except Exception as e:
                print(f"Error in Run method: {e}")
        dialog.Destroy()

SelectViasByNet().register()

class NetNameDialog(wx.Dialog):
    def __init__(self, *args, **kw):
        super(NetNameDialog, self).__init__(*args, **kw)
        self.InitUI()

    def InitUI(self):
        print("Initializing UI")
        try:
            board = pcbnew.GetBoard()
            nets = board.GetNetsByName()
            net_names = ["All"] + [str(net_name) for net_name in nets.keys()]

            vbox = wx.BoxSizer(wx.VERTICAL)

            # Net Name
            hbox1 = wx.BoxSizer(wx.HORIZONTAL)
            st1 = wx.StaticText(self, label='Net Name')
            st1.SetToolTip("Select the net name from the list. 'All' selects all nets.")
            hbox1.Add(st1, flag=wx.RIGHT, border=8)
            self.net_name_choice = wx.Choice(self, choices=net_names)
            self.net_name_choice.SetSelection(0)  # Select "All" by default
            self.net_name_choice.SetToolTip("Choose the net for which you want to select vias.")
            hbox1.Add(self.net_name_choice, proportion=1)
            vbox.Add(hbox1, flag=wx.ALL | wx.EXPAND, border=5)

            # Zone Checkbox
            hbox2 = wx.BoxSizer(wx.HORIZONTAL)
            self.zone_checkbox = wx.CheckBox(self, label="Only under selected Zone")
            self.zone_checkbox.SetValue(True)
            self.zone_checkbox.SetToolTip("Check this box to only select vias under the currently selected zone.")
            hbox2.Add(self.zone_checkbox, flag=wx.RIGHT, border=8)
            vbox.Add(hbox2, flag=wx.ALL | wx.EXPAND, border=5)

            # Min Size Drop-down
            hbox3 = wx.BoxSizer(wx.HORIZONTAL)
            st2 = wx.StaticText(self, label='Min Size (mm)')
            st2.SetToolTip("Select the minimum via size (diameter) in millimeters.")
            hbox3.Add(st2, flag=wx.RIGHT, border=8)
            self.min_size_choice = wx.Choice(self)
            self.min_size_choice.SetToolTip("Choose the smallest via size to include.")
            hbox3.Add(self.min_size_choice, proportion=1)
            vbox.Add(hbox3, flag=wx.ALL | wx.EXPAND, border=5)

            # Max Size Drop-down
            hbox4 = wx.BoxSizer(wx.HORIZONTAL)
            st3 = wx.StaticText(self, label='Max Size (mm)')
            st3.SetToolTip("Select the maximum via size (diameter) in millimeters.")
            hbox4.Add(st3, flag=wx.RIGHT, border=8)
            self.max_size_choice = wx.Choice(self)
            self.max_size_choice.SetToolTip("Choose the largest via size to include.")
            hbox4.Add(self.max_size_choice, proportion=1)
            vbox.Add(hbox4, flag=wx.ALL | wx.EXPAND, border=5)

            # Populate min and max sizes
            sizes = self.get_via_sizes(board)
            self.min_size_choice.SetItems(sizes)
            self.min_size_choice.SetSelection(0)  # Select the smallest size
            self.max_size_choice.SetItems(sizes)
            self.max_size_choice.SetSelection(len(sizes) - 1)  # Select the largest size
            print(f"Sizes loaded: {sizes}")

            # Action Drop-down
            hbox5 = wx.BoxSizer(wx.HORIZONTAL)
            st4 = wx.StaticText(self, label='Action')
            st4.SetToolTip("Select the action to perform on the selected vias.")
            hbox5.Add(st4, flag=wx.RIGHT, border=8)
            self.action_choice = wx.Choice(self, choices=["Highlight", "Delete", "Change Size"])
            self.action_choice.SetSelection(0)
            self.action_choice.SetToolTip("Choose what to do with the selected vias.")
            hbox5.Add(self.action_choice, proportion=1)
            vbox.Add(hbox5, flag=wx.ALL | wx.EXPAND, border=5)

            # Via Sizes Drop-down
            hbox6 = wx.BoxSizer(wx.HORIZONTAL)
            st5 = wx.StaticText(self, label='New Size')
            st5.SetToolTip("Select the new size for vias if 'Change Size' is selected.")
            hbox6.Add(st5, flag=wx.RIGHT, border=8)
            self.via_size_choice = wx.Choice(self)
            self.via_size_choice.SetToolTip("Choose the new via size if changing size.")
            hbox6.Add(self.via_size_choice, proportion=1)
            vbox.Add(hbox6, flag=wx.ALL | wx.EXPAND, border=5)

            # Populate via sizes
            self.via_size_choice.SetItems(sizes)
            print(f"Via sizes loaded: {sizes}")

            # Ok and Close buttons
            hbox7 = wx.BoxSizer(wx.HORIZONTAL)
            okButton = wx.Button(self, label='Ok')
            okButton.SetToolTip("Click to execute the selected actions on the vias.")
            closeButton = wx.Button(self, label='Close')
            closeButton.SetToolTip("Click to close the dialog without making changes.")
            hbox7.Add(okButton)
            hbox7.Add(closeButton, flag=wx.LEFT | wx.BOTTOM, border=5)
            vbox.Add(hbox7, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=10)
            
            # Additional static text
            info_text = wx.StaticText(self, label="Vias will only be deleted on exit")
            vbox.Add(info_text, flag=wx.ALL | wx.EXPAND, border=1)
            info_text = wx.StaticText(self, label="if the action is chosen.")
            vbox.Add(info_text, flag=wx.ALL | wx.EXPAND, border=1)

            self.SetSizer(vbox)

            okButton.Bind(wx.EVT_BUTTON, self.OnOk)
            closeButton.Bind(wx.EVT_BUTTON, self.OnClose)

            self.SetSize((350, 430))
            self.SetTitle('Kicad Via Tool')

            # Center the dialog on the screen
            self.CenterOnScreen()
        except Exception as e:
            print(f"Error in InitUI: {e}")

    def get_via_sizes(self, board):
        try:
            sizes = []
            design_settings = board.GetDesignSettings()
            if hasattr(design_settings, 'm_ViasDimensionsList'):
                vias_dimensions_list = design_settings.m_ViasDimensionsList
                for via_dimension in vias_dimensions_list:
                    try:
                        via_diameter = via_dimension.m_Diameter / 1e6  # Convert from nm to mm
                        via_drill = via_dimension.m_Drill / 1e6  # Convert from nm to mm
                        if via_diameter > 0 and via_drill > 0:
                            size_str = f"{via_diameter:.3f} / {via_drill:.3f} mm"
                            sizes.append(size_str)
                    except Exception as e:
                        print(f"Error accessing via sizes: {e}")
            print(f"Sizes: {sizes}")
            return sizes
        except Exception as e:
            print(f"Error in get_via_sizes: {e}")
            return []

    def OnOk(self, e):
        try:
            self.net_name = self.net_name_choice.GetString(self.net_name_choice.GetSelection())
            self.use_zone = self.zone_checkbox.GetValue()
            self.min_size = float(self.min_size_choice.GetString(self.min_size_choice.GetSelection()).split('/')[0].strip())
            self.max_size = float(self.max_size_choice.GetString(self.max_size_choice.GetSelection()).split('/')[0].strip())
            self.action = self.action_choice.GetString(self.action_choice.GetSelection())
            if self.action == "Change Size":
                via_size_str = self.via_size_choice.GetString(self.via_size_choice.GetSelection()).split('/')
                self.new_drill_size = float(via_size_str[1].strip().split()[0])
                self.new_diameter = float(via_size_str[0].strip())
            else:
                self.new_drill_size = 0.0
                self.new_diameter = 0.0
            print(f"Dialog values: net_name={self.net_name}, use_zone={self.use_zone}, min_size={self.min_size}, max_size={self.max_size}, action={self.action}, new_drill_size={self.new_drill_size}, new_diameter={self.new_diameter}")
            self.EndModal(wx.ID_OK)
        except Exception as e:
            print(f"Error in OnOk: {e}")

    def OnClose(self, e):
        self.EndModal(wx.ID_CANCEL)

def get_selected_zone():
    try:
        board = pcbnew.GetBoard()
        selected_zones = [zone for zone in board.Zones() if zone.IsSelected()]
        if not selected_zones:
            return None
        return selected_zones[0]
    except Exception as e:
        print(f"Error in get_selected_zone: {e}")
        return None

def is_point_in_polygon(point, polygon):
    try:
        x, y = point.x, point.y
        n = len(polygon)
        inside = False

        p1x, p1y = polygon[0]
        for i in range(n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside
    except Exception as e:
        print(f"Error in is_point_in_polygon: {e}")
        return False

def get_zone_vertices(zone):
    try:
        vertices = []
        zone_outline = zone.Outline()
        for i in range(zone_outline.OutlineCount()):
            outline = zone_outline.Outline(i)
            for j in range(outline.GetPointCount()):
                point = outline.GetPoint(j)
                vertices.append((point.x, point.y))
        return vertices
    except Exception as e:
        print(f"Error in get_zone_vertices: {e}")
        return []

def is_via_in_zone(via_pos, zone):
    try:
        zone_vertices = get_zone_vertices(zone)
        return is_point_in_polygon(via_pos, zone_vertices)
    except Exception as e:
        print(f"Error in is_via_in_zone: {e}")
        return False

def select_vias_by_net(net_name, use_zone, zone, min_size, max_size, action, new_drill_size, new_diameter):
    print("Starting select_vias_by_net function")
    try:
        board = pcbnew.GetBoard()
        nets = board.GetNetsByName()
        if net_name == "All":
            net_codes = [net.GetNetCode() for net in nets.values()]
        else:
            net_dict = {str(net_name): net.GetNetCode() for net_name, net in nets.items()}
            if net_name not in net_dict:
                print(f"Net name {net_name} not found in net list.")
                return
            net_codes = [net_dict[net_name]]

        for item in board.GetTracks():
            if isinstance(item, pcbnew.PCB_VIA):
                if item.GetNetCode() in net_codes:
                    via_size = item.GetWidth() / 1e6  # Convert from nm to mm
                    print(f"Checking via at position {item.GetPosition()}: size {via_size} mm")
                    if min_size <= via_size <= max_size:
                        if use_zone:
                            via_pos = item.GetPosition()
                            if not is_via_in_zone(via_pos, zone):
                                continue
                        item.SetSelected()
                        if action == "Delete":
                            board.Remove(item)
                            print(f"Via at position {item.GetPosition()} deleted")
                        elif action == "Change Size":
                            print(f"Changing via at position {item.GetPosition()} to drill size {new_drill_size} and diameter {new_diameter}")
                            item.SetDrill(int(new_drill_size * 1e6))  # Convert from mm to nm
                            item.SetWidth(int(new_diameter * 1e6))  # Convert from mm to nm
                            print(f"Via at position {item.GetPosition()} updated with new drill size {new_drill_size} and diameter {new_diameter}")

        pcbnew.Refresh()
    except Exception as e:
        print(f"Error in select_vias_by_net: {e}")

SelectViasByNet().register()
