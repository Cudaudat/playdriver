import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
import inspect
import sys
import re
import platform

# from logger import logger
# logger.set_console_level("DEBUG")
# logger.enable_call_stack_trace(True, depth=3)

BASEDIR, CURRENT_FOLDER, CURRENT_FILE = os.path.dirname(f'{__file__}'), os.path.dirname(f'{__file__}').split('\\')[-1], __file__
# ANSI color codes
class Colors:
    """ANSI color codes for terminal output"""
    """# Text colors"""
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    """# Background colors"""
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'
    """# Styles"""
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""
    COLORS = { 'DEBUG': Colors.CYAN, 'INFO': Colors.GREEN, 'WARNING': Colors.YELLOW, 'ERROR': Colors.RED, 'CRITICAL': Colors.BG_RED + Colors.WHITE}
    def format(self, record):
        """# Add color to levelname"""
        if record.levelname in self.COLORS: record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{Colors.RESET}"
        """# Add color to message based on level"""
        if record.levelname in self.COLORS: record.msg = f"{self.COLORS[record.levelname]}{record.msg}{Colors.RESET}"
        return super().format(record)

class CallStackConfig:
    """Advanced configuration for call stack tracing"""
    
    def __init__(self):
        # Basic settings
        self.enabled = False
        self.depth = 3
        self.show_immediate_caller = False
        
        # Advanced settings
        self.auto_enable_on_debug = True  # Auto enable when debug level
        self.show_file_path = False       # Show full file path or basename only
        self.show_line_numbers = True     # Show line numbers
        self.show_function_params = False # Show function parameters in stack
        self.exclude_modules = ['logger.py', 'logging']  # Modules to skip
        self.include_only_modules = []    # Only show these modules (empty = all)
        
        # Smart Tree specific settings
        self.show_full_path_no_hidden_for_cross_files = False  # 🚀 Show full path for cross-file calls
        self.show_full_path_for_cross_files = False  # 🚀 Show full path for cross-file calls
        self.path_compression_level = "smart"        # 🚀 NEW: "none", "smart", "aggressive"
        self.auto_compression_for_errors = True      # 🚀 NEW: Auto compress for readability
        
        # Display modes
        self.display_mode = 'arrows'      # 'arrows', 'tree', 'compact', 'detailed'
        self.max_param_length = 50        # Max length for parameters display
        self.colorize_stack = True        # Use colors in stack trace
        
        # Performance settings
        self.cache_stack_info = True      # Cache repeated stack patterns
        self.skip_internal_frames = 3     # Frames to skip (logger internals)
        
        # Context-aware settings
        self.different_depth_for_errors = 5    # More depth for error logs
        self.show_caller_for_warnings = True   # Auto show caller for warnings
        self.minimal_mode_for_info = False     # Minimal display for info logs

class PathCompressor:
    """🚀 Smart path compression engine for better readability"""
    
    def __init__(self, call_stack_config: CallStackConfig):
        # Detect common paths for compression
        self.project_root = os.getcwd()
        self.user_home = os.path.expanduser("~")
        self.python_path = os.path.dirname(sys.executable)
        self.call_stack_config = call_stack_config

        # Pre-compile regex patterns for performance
        self.system_patterns = [
            (re.compile(rf'{re.escape(self.python_path)}'), r'~\Python'),
            (re.compile(rf'{re.escape(self.user_home)}'), '~'),
            (re.compile(r'C:\\Windows\\System32'), r'...\System32'),
            (re.compile(r'.*\\site-packages\\'), r'...\site-packages\\'),
        ]
        
        # Cache for processed paths
        self._cache = {}
        
    def compress_path(self, full_path: str, compression_level: str = "smart") -> str:
        """
        Compress path based on compression level
        
        Args:
            full_path: Full absolute path
            compression_level: "none", "smart", "aggressive"
        """
        if compression_level == "none":
            return full_path
            
        # Check cache first
        cache_key = f"{full_path}_{compression_level}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        compressed = self._compress_path_internal(full_path, compression_level)
        self._cache[cache_key] = compressed
        return compressed
    
    def _compress_path_internal(self, full_path: str, level: str) -> str:
        """Internal path compression logic"""
        if self.call_stack_config.show_full_path_no_hidden_for_cross_files: return full_path
        # Project files - always show relative to project
        if full_path.startswith(self.project_root):
            relative = os.path.relpath(full_path, self.project_root)
            if level == "aggressive" and len(relative) > 40:
                # Super aggressive - show only filename for long project paths
                # return f"{os.path.basename(full_path)}"
                return f"...\\{os.path.basename(full_path)}"
            return relative
        
        # Apply system path patterns
        # 🚀 FIXED: Use string replacement instead of regex sub to avoid escape issues
        for pattern, replacement in self.system_patterns:
            if pattern.search(full_path):
                # Use simple string replacement instead of regex sub
                match_obj = pattern.search(full_path)
                if match_obj:
                    matched_text = match_obj.group()
                    compressed = full_path.replace(matched_text, replacement, 1)
                    # return compressed
                    
                    if level == "aggressive" and len(compressed) > 50:
                        # Aggressive mode - further truncate middle
                        parts = compressed.split('\\')
                        if len(parts) > 3:
                            return f"{parts[0]}\\...\\{parts[-2]}\\{parts[-1]}"
                    return compressed
        
        # Fallback for unknown paths
        if level == "aggressive":
            return f"...\\{os.path.basename(full_path)}"
        elif len(full_path) > 60:
            # Show start and end for very long paths
            return f"{full_path[:20]}...{full_path[-30:]}"
        
        return full_path

class CallStackTracer:
    """Class để trace call stack với beautiful formatting"""
    
    @staticmethod
    def get_call_stack(depth: int = 3, skip_frames: int = 3) -> str:
        """
        Lấy call stack với formatting đẹp
        
        Args:
            depth: Số lượng frames tối đa để trace
            skip_frames: Số frames cần skip (logger internals)
            
        Returns:
            Formatted call stack string
        """
        try:
            frame = inspect.currentframe()
            call_stack = []
            
            # Skip internal logger frames
            for _ in range(skip_frames):
                if frame:
                    frame = frame.f_back
            
            # Collect call stack
            for i in range(depth):
                if not frame:
                    break
                    
                filename = os.path.basename(frame.f_code.co_filename)
                function_name = frame.f_code.co_name
                line_number = frame.f_lineno
                
                # Format: filename:function:line
                call_info = f"{filename}:{function_name}:{line_number}"
                call_stack.append(call_info)
                
                frame = frame.f_back
            
            if call_stack:
                # Format with arrows to show call direction
                stack_str = " ➤ ".join(reversed(call_stack))
                return f"📍 Call Stack: {stack_str}"
            else:
                return ""
                
        except Exception as e:
            return f"📍 Call Stack Error: {str(e)}"
    
    @staticmethod
    def get_immediate_caller(skip_frames: int = 3) -> str:
        """
        Lấy thông tin của caller trực tiếp (1 level up)
        
        Args:
            skip_frames: Số frames cần skip
            
        Returns:
            Caller information string
        """
        try:
            frame = inspect.currentframe()
            
            # Skip internal logger frames
            for _ in range(skip_frames):
                if frame:
                    frame = frame.f_back
            
            if frame:
                filename = os.path.basename(frame.f_code.co_filename)
                function_name = frame.f_code.co_name
                line_number = frame.f_lineno
                
                return f"👤 Called by: {filename}:{function_name}:{line_number}"
            else:
                return "👤 Called by: Unknown"
                
        except Exception as e:
            return f"👤 Caller Error: {str(e)}"

class SingletonLogger:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SingletonLogger, cls).__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance

    def _initialize_logger(self):
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'): os.makedirs('logs')

        # Initialize advanced call stack configuration
        self.call_stack_config = CallStackConfig()
        self._stack_cache = {}  # Cache for repeated patterns
        
        # Initialize path compressor
        self.path_compressor = PathCompressor(self.call_stack_config)

        # Create logger
        self.logger = logging.getLogger('iOS_Trym')
        self.logger.setLevel(logging.DEBUG)  # Set root logger to DEBUG

        # Create formatters
        file_formatter = logging.Formatter( '%(asctime)s - %(name)s - %(levelname)s - [%(pathname)s:%(lineno)d] - %(message)s' )
        console_formatter = ColoredFormatter( '%(asctime)s - %(name)s - %(levelname)s - [%(pathname)s:%(lineno)d] - %(message)s' )

        # File handler (with rotation)
        log_file = os.path.join('logs', f'app_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # File handler always logs everything
        file_handler.setFormatter(file_formatter)

        # Console handler
        console_handler = logging.StreamHandler()
        # Set console level based on environment or config
        console_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        console_handler.setLevel(getattr(logging, console_level))
        console_handler.setFormatter(console_formatter)

        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def configure_call_stack_tracing(self, **kwargs):
        """
        Comprehensive configuration for call stack tracing
        
        Args:
            enabled (bool): Enable/disable tracing
            depth (int): Call stack depth
            show_immediate_caller (bool): Show only immediate caller
            auto_enable_on_debug (bool): Auto enable when debug level
            display_mode (str): 'arrows', 'tree', 'compact', 'detailed'
            show_file_path (bool): Show full path or basename
            exclude_modules (list): Modules to exclude from trace
            different_depth_for_errors (int): Different depth for error logs
            colorize_stack (bool): Use colors in stack trace
        """
        config = self.call_stack_config
        
        # Update configuration
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        # Log configuration change
        if config.enabled:
            self.logger.info(f"🔍 Call Stack Tracing CONFIGURED:")
            self.logger.info(f"   📊 Mode: {config.display_mode} | Depth: {config.depth}")
            self.logger.info(f"   🎯 Show caller: {config.show_immediate_caller}")
            self.logger.info(f"   🚫 Exclude: {config.exclude_modules}")
            if config.different_depth_for_errors != config.depth:
                self.logger.info(f"   ❌ Error depth: {config.different_depth_for_errors}")
        else:
            self.logger.info("🔍 Call Stack Tracing DISABLED")

    def enable_call_stack_trace(self, enabled: bool = True, depth: int = 3, show_immediate_caller: bool = False):
        """
        Simple enable/disable method (backward compatibility)
        """
        self.configure_call_stack_tracing(
            enabled=enabled,
            depth=depth,
            show_immediate_caller=show_immediate_caller
        )

    def set_console_level(self, level: str):
        """Set console logging level dynamically với auto call stack detection"""
        level = level.upper()
        if level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            raise ValueError(f"Invalid log level: {level}")
        
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                handler.setLevel(getattr(logging, level))
                
        # Auto-enable call stack tracing for DEBUG level
        if level == 'DEBUG' and self.call_stack_config.auto_enable_on_debug:
            if not self.call_stack_config.enabled:
                self.configure_call_stack_tracing(
                    enabled=True,
                    depth=3,
                    display_mode='compact',
                    show_immediate_caller=True
                )
                self.logger.info(f"🔍 Auto-enabled call stack tracing for DEBUG level")
        
        self.logger.info(f"Console logging level set to {level}")

    def _should_show_stack_for_level(self, level: int) -> tuple:
        """
        Determine if stack should be shown và with what configuration
        Returns: (should_show, depth, show_caller)
        """
        config = self.call_stack_config
        
        if not config.enabled:
            return False, 0, False
        
        # Different behavior for different log levels
        if level >= logging.ERROR:
            # Errors: show detailed stack
            return True, config.different_depth_for_errors, False
        elif level >= logging.WARNING and config.show_caller_for_warnings:
            # Warnings: show caller
            return True, 2, True
        elif level >= logging.INFO and config.minimal_mode_for_info:
            # Info: minimal mode
            return True, 1, True
        else:
            # Default behavior
            return True, config.depth, config.show_immediate_caller

    def _format_stack_with_style(self, call_stack: list, show_caller_only: bool = False) -> str:
        """
        Format call stack với different display modes và smart file detection
        """
        config = self.call_stack_config
        
        if not call_stack:
            return ""
        
        if show_caller_only and call_stack:
            # Show only immediate caller
            caller = call_stack[0]
            if config.colorize_stack:
                return f"\n    {Colors.CYAN}👤 Called by: {caller}{Colors.RESET}"
            else:
                return f"\n    👤 Called by: {caller}"
        
        # Format based on display mode
        if config.display_mode == 'arrows':
            stack_str = " ➤ ".join(reversed(call_stack))
            icon = "📍 Call Stack: "
        elif config.display_mode == 'tree':
            # SMART TREE MODE với same file detection
            stack_str = self._format_smart_tree(call_stack)
            icon = "🌳 Call Tree:\n    "
        elif config.display_mode == 'compact':
            # Show only first and last
            if len(call_stack) > 2:
                stack_str = f"{call_stack[-1]} ➤ ... ➤ {call_stack[0]}"
            else:
                stack_str = " ➤ ".join(reversed(call_stack))
            icon = "📍 "
        elif config.display_mode == 'detailed':
            stack_lines = []
            for i, item in enumerate(reversed(call_stack)):
                stack_lines.append(f"  {i+1}. {item}")
            stack_str = "\n".join(stack_lines)
            icon = "📋 Detailed Stack:\n"
        else:
            # Default arrows
            stack_str = " ➤ ".join(reversed(call_stack))
            icon = "📍 Call Stack: "
        
        if config.colorize_stack: return f"\n    {Colors.BLUE}{icon}{stack_str}{Colors.RESET}"
        else: return f"\n    {icon}{stack_str}"

    def _format_smart_tree(self, call_stack: list) -> str:
        """
        Format call stack như tree với smart file detection và path compression
        - Same file: chỉ hiển thị function name
        - Different file: hiển thị compressed path:function (if show_full_path_for_cross_files enabled)
        """
        if not call_stack:
            return ""
        
        # Parse call stack items để extract file và function info
        parsed_stack = []
        for item in call_stack:
            # 🚀 FIXED: Handle Windows paths correctly (C:\path contains :)
            # Use rsplit to split from the right, limiting splits
            parts = item.rsplit(':', 2)  # Split from right, max 2 splits
            
            if len(parts) == 3:
                # Format: "path:function:line"
                file_part = parts[0]
                function_part = parts[1]
                line_part = parts[2]
            elif len(parts) == 2:
                # Format: "path:function" (no line)
                file_part = parts[0]
                function_part = parts[1]
                line_part = ""
            else:
                # Fallback for malformed items
                file_part = 'unknown'
                function_part = item
                line_part = ''
                
            parsed_stack.append({
                'file': file_part,
                'function': function_part,
                'line': line_part,
                'original': item
            })
        
        # Determine "current file" (file của frame đầu tiên)
        current_file = parsed_stack[0]['file'] if parsed_stack else None
        
        # Build smart tree
        tree_lines = []
        reversed_stack = list(reversed(parsed_stack))
        
        for i, frame in enumerate(reversed_stack):
            # Determine indentation
            indent = "    " * i  # 4 spaces per level
            
            # Determine tree connector
            if i == 0:
                connector = "└─── "
            else:
                connector = "└─── "
            
            # Smart formatting based on file comparison
            if frame['file'] == current_file:
                # Same file - chỉ hiển thị function
                display_name = f"{frame['function']}()"
                if self.call_stack_config.colorize_stack:
                    display_name = f"{Colors.GREEN}{current_file}:{display_name}:{frame['line']}{Colors.RESET}"
            else:
                # Different file - apply smart path compression
                if self.call_stack_config.show_full_path_for_cross_files:
                    # 🚀 Apply smart path compression
                    file_display = self.path_compressor.compress_path(
                        frame['file'], 
                        self.call_stack_config.path_compression_level
                    )
                else:
                    # Show only basename (default behavior)
                    file_display = os.path.basename(frame['file'])
                
                if frame['line']:
                    display_name = f"{file_display}:{frame['function']}:{frame['line']}"
                else:
                    display_name = f"{file_display}:{frame['function']}"
                
                if self.call_stack_config.colorize_stack:
                    if self.call_stack_config.show_full_path_for_cross_files:
                        # Full path coloring với path compression - make compressed path prominent
                        # Use different colors for project vs system files
                        if frame['file'].startswith(self.path_compressor.project_root):
                            # Project file - cyan
                            file_color = f"{Colors.CYAN}{file_display}{Colors.RESET}"
                        else:
                            # System file - bold yellow
                            file_color = f"{Colors.BOLD}{Colors.YELLOW}{file_display}{Colors.RESET}"
                        
                        display_name = f"{file_color}:{Colors.GREEN}{frame['function']}{Colors.RESET}"
                    else:
                        # Basename coloring
                        display_name = f"{Colors.YELLOW}{file_display}{Colors.RESET}:{Colors.GREEN}{frame['function']}{Colors.RESET}"
                    
                    if frame['line']:
                        display_name += f":{Colors.CYAN}{frame['line']}{Colors.RESET}"
            
            tree_lines.append(f"{indent}{connector}{display_name}")
        
        return "\n    ".join(tree_lines)

    def _get_enhanced_call_stack(self, depth: int, skip_frames: int) -> list:
        """
        Enhanced call stack collection với filtering và caching
        """
        config = self.call_stack_config
        
        try:
            frame = inspect.currentframe()
            call_stack = []
            
            # Skip internal logger frames
            for _ in range(skip_frames):
                if frame:
                    frame = frame.f_back
            
            # Collect call stack
            for i in range(depth):
                if not frame:
                    break
                    
                filename = frame.f_code.co_filename
                function_name = frame.f_code.co_name
                line_number = frame.f_lineno
                
                # Filter by modules
                basename = os.path.basename(filename)
                
                # Check exclude list
                if config.exclude_modules:
                    if any(excluded in basename for excluded in config.exclude_modules):
                        frame = frame.f_back
                        continue
                
                # Check include list
                if config.include_only_modules:
                    if not any(included in basename for included in config.include_only_modules):
                        frame = frame.f_back
                        continue
                
                # Smart path formatting based on config
                if config.show_file_path:
                    # Show full path for config
                    file_part = filename
                else:
                    # 🚀 NEW LOGIC: For smart tree with full paths, always pass full path so compression can work
                    if (config.display_mode == 'tree' and 
                        config.show_full_path_for_cross_files):
                        # Smart tree needs full path for compression engine
                        file_part = filename
                    else:
                        # Default behavior: basename only
                        file_part = basename
                
                if config.show_line_numbers:
                    call_info = f"{file_part}:{line_number}:{function_name}"
                else:
                    call_info = f"{file_part}:{function_name}"
                
                call_stack.append(call_info)
                frame = frame.f_back
            
            return call_stack
                
        except Exception as e:
            return [f"Stack Error: {str(e)}"]

    def _format_message_with_stack(self, msg: str, level: int, force_stack: bool = False) -> str:
        """
        Enhanced message formatting với context-aware stack display
        
        Args:
            msg: Original message
            level: Log level
            force_stack: Force show stack even if config disabled (e.g., stack_info=True)
        """
        # Check if we should show stack
        if force_stack:
            # Explicit stack_info=True, always show
            # But still respect display settings for consistency
            should_show = True
            # Use configured depth or sensible default
            depth = self.call_stack_config.depth if self.call_stack_config.depth > 0 else 5
            # For forced stack, don't use caller-only mode
            show_caller = False
            
            # 💡 NEW: Temporarily enable for formatting if disabled
            was_disabled = not self.call_stack_config.enabled
            if was_disabled:
                # Use sensible defaults for forced stack when config disabled
                # But preserve display mode if set
                if not self.call_stack_config.display_mode:
                    self.call_stack_config.display_mode = 'arrows'
        else:
            # Use normal config-based logic
            should_show, depth, show_caller = self._should_show_stack_for_level(level)
            was_disabled = False
        
        if not should_show:
            return msg
        
        # Get call stack - use one more skip frame for stack_info calls
        skip_frames = self.call_stack_config.skip_internal_frames
        if force_stack:
            # For stack_info=True calls, we might need different skip frames
            # depending on how deep we are in the logger
            skip_frames = 4  # Typically need to skip more frames for explicit stack_info
            
        call_stack = self._get_enhanced_call_stack(depth, skip_frames)
        
        if not call_stack:
            return msg
        
        # Format stack with special indicator for forced stack
        if force_stack and was_disabled:
            # Add special prefix to indicate this is from stack_info=True
            stack_info = self._format_stack_with_style(call_stack, show_caller)
            # Replace the icon to indicate forced stack
            stack_info = stack_info.replace("📍", "🔍")  # Different icon for forced
            stack_info = stack_info.replace("🌳", "🔍")  # For tree mode too
        else:
            stack_info = self._format_stack_with_style(call_stack, show_caller)
        
        # Combine message với stack info
        return f"{msg}{stack_info}"

    def _log(self, level, msg, *args, **kwargs):
        # Get the caller's frame
        import sys
        frame = inspect.currentframe()
        try:
            # Go up two frames to get the actual caller
            caller_frame = frame.f_back.f_back
            filename = caller_frame.f_code.co_filename
            lineno = caller_frame.f_lineno
            
            # Check for explicit stack_info parameter
            stack_info_requested = kwargs.get('stack_info', False)
            
            # Enhance message với context-aware call stack
            # Force stack if stack_info=True even when config disabled
            enhanced_msg = self._format_message_with_stack(msg, level, force_stack=stack_info_requested)
            
            # Handle exc_info properly
            exc_info = kwargs.get('exc_info')
            if exc_info:
                if isinstance(exc_info, BaseException):
                    exc_info = (type(exc_info), exc_info, exc_info.__traceback__)
                elif not isinstance(exc_info, tuple):
                    exc_info = sys.exc_info()
            
            # Handle stack_info for Python logging compatibility
            # If we already enhanced the message, don't pass stack_info to avoid duplicate
            if stack_info_requested:
                # We already added our custom stack to the message
                # Don't pass stack_info to Python to avoid duplicate
                kwargs = {k: v for k, v in kwargs.items() if k != 'stack_info'}
                stack_info_param = False
            else:
                # No stack_info requested, nothing to do
                stack_info_param = False
            
            # Create a new logger with the caller's information
            logger = logging.getLogger('iOS_Trym')
            # Create a LogRecord with the caller's information
            record = logging.LogRecord(
                name='iOS_Trym', level=level, pathname=filename, lineno=lineno, 
                msg=enhanced_msg, args=args, exc_info=exc_info
            )
            
            # Add stack_info to record for Python logging
            if stack_info_param:
                record.stack_info = self._get_python_stack_info()
            
            # Log the record
            logger.handle(record)
        finally:
            del frame
    
    def _get_python_stack_info(self):
        """Get stack info in Python logging format"""
        import traceback
        stack = traceback.format_stack()
        # Remove logger internal frames
        if len(stack) > 3:
            stack = stack[:-3]
        return ''.join(stack)

    def debug(self, msg, *args, **kwargs):
        self._log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._log(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._log(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._log(logging.CRITICAL, msg, *args, **kwargs)

    # ========================================
    # 🎯 CONVENIENCE METHODS FOR CALL TRACING
    # ========================================
    
    def trace_function_entry(self, function_name: str = None, **params):
        """
        Log function entry với parameters
        
        Args:
            function_name: Tên function (auto-detect nếu None)
            **params: Function parameters để log
        """
        if not function_name:
            # Auto-detect function name
            frame = inspect.currentframe().f_back
            function_name = frame.f_code.co_name
        
        params_str = ", ".join([f"{k}={v}" for k, v in params.items()]) if params else "no params"
        self.debug(f"🔵 ENTER {function_name}({params_str})")
    
    def trace_function_exit(self, function_name: str = None, result=None):
        """
        Log function exit với result
        
        Args:
            function_name: Tên function (auto-detect nếu None)
            result: Return value để log
        """
        if not function_name:
            # Auto-detect function name
            frame = inspect.currentframe().f_back
            function_name = frame.f_code.co_name
        
        result_str = f" -> {result}" if result is not None else ""
        self.debug(f"🔴 EXIT {function_name}{result_str}")
    
    def trace_function_call(self, target_function: str, **params):
        """
        Log khi sắp gọi function khác
        
        Args:
            target_function: Tên function sắp được gọi
            **params: Parameters sẽ pass vào function
        """
        params_str = ", ".join([f"{k}={v}" for k, v in params.items()]) if params else "no params"
        self.debug(f"📞 CALLING {target_function}({params_str})")

    # ========================================
    # 🎯 QUICK CONFIGURATION PRESETS
    # ========================================
    
    def use_development_tracing(self):
        """Preset for development environment"""
        self.configure_call_stack_tracing(
            enabled=True,
            depth=4,
            display_mode='arrows',
            show_immediate_caller=False,
            colorize_stack=True,
            different_depth_for_errors=6,
            show_caller_for_warnings=True,
            exclude_modules=['logger.py']
        )
        self.logger.info("🔧 Development tracing preset activated")
    
    def use_production_tracing(self):
        """Preset for production environment"""
        self.configure_call_stack_tracing(
            enabled=True,
            depth=2,
            display_mode='compact',
            show_immediate_caller=True,
            colorize_stack=False,
            different_depth_for_errors=4,
            show_caller_for_warnings=True,
            exclude_modules=['logger.py', 'logging']
        )
        self.logger.info("🏭 Production tracing preset activated")
    
    def use_debugging_tracing(self):
        """Preset for intensive debugging"""
        self.configure_call_stack_tracing(
            enabled=True,
            depth=6,
            display_mode='detailed',
            show_immediate_caller=False,
            colorize_stack=True,
            different_depth_for_errors=8,
            show_caller_for_warnings=True,
            show_file_path=True,
            exclude_modules=[]  # Show everything
        )
        self.logger.info("🐛 Debugging tracing preset activated")
    
    def use_minimal_tracing(self):
        """Preset for minimal overhead"""
        self.configure_call_stack_tracing(
            enabled=True,
            depth=1,
            display_mode='compact',
            show_immediate_caller=True,
            colorize_stack=False,
            minimal_mode_for_info=True,
            exclude_modules=['logger.py', 'logging']
        )
        self.logger.info("⚡ Minimal tracing preset activated")

    def use_smart_tree_tracing(self):
        """🚀 NEW: Preset for smart tree with full paths"""
        self.configure_call_stack_tracing(
            enabled=True,
            depth=5,
            display_mode='tree',
            show_immediate_caller=False,
            colorize_stack=True,
            show_full_path_for_cross_files=True,  # 🚀 Enable full paths!
            path_compression_level="smart",       # 🚀 NEW: Smart compression
            different_depth_for_errors=7,
            show_caller_for_warnings=True,
            exclude_modules=['logger.py']
        )
        self.logger.info("🌳 Smart Tree tracing với full paths activated!")

    def use_compressed_tree_tracing(self):
        """🚀 NEW: Preset for heavily compressed paths (great for AsyncIO debugging)"""
        self.configure_call_stack_tracing(
            enabled=True,
            depth=6,
            display_mode='tree',
            show_immediate_caller=False,
            colorize_stack=True,
            show_full_path_for_cross_files=True,
            path_compression_level="aggressive",  # 🚀 Aggressive compression
            different_depth_for_errors=8,
            show_caller_for_warnings=True,
            exclude_modules=['logger.py']
        )
        self.logger.info("🗜️  Compressed Tree tracing activated - perfect for deep AsyncIO stacks!")

    def use_no_compression_tracing(self):
        """🚀 NEW: Full absolute paths with no compression (maximum detail)"""
        self.configure_call_stack_tracing(
            enabled=True,
            depth=6,
            display_mode='tree',
            show_immediate_caller=False,
            colorize_stack=True,
            show_full_path_for_cross_files=True,
            path_compression_level="none",        # 🚀 No compression
            different_depth_for_errors=8,
            show_caller_for_warnings=True,
            exclude_modules=[]  # Show everything
        )
        self.logger.info("📁 Full absolute paths mode - maximum debugging detail!")

    def enable_full_path_mode(self):
        """🚀 Quick method to enable full path display for cross-files"""
        self.configure_call_stack_tracing(
            show_full_path_for_cross_files=True,
            display_mode='tree',  # Works best with tree mode
            path_compression_level="smart"  # 🚀 Default to smart compression
        )
        self.logger.info("📁 Full path mode enabled for cross-file calls!")

    def disable_full_path_mode(self):
        """Disable full path display, back to basename only"""
        self.configure_call_stack_tracing(
            show_full_path_for_cross_files=False
        )
        self.logger.info("📁 Full path mode disabled, using basename only")

    def set_compression_level(self, level: str):
        """🚀 NEW: Quick method to change path compression level"""
        if level not in ["none", "smart", "aggressive"]:
            raise ValueError(f"Invalid compression level: {level}. Use 'none', 'smart', or 'aggressive'")
        
        self.configure_call_stack_tracing(
            path_compression_level=level,
            show_full_path_for_cross_files=True  # Auto-enable full paths when setting compression
        )
        
        level_descriptions = {
            "none": "Full absolute paths - maximum detail",
            "smart": "Compressed system paths, relative project paths",
            "aggressive": "Heavily compressed - best for deep stacks"
        }
        
        self.logger.info(f"🗜️  Path compression set to '{level}': {level_descriptions[level]}")

    def get_stack_info_behavior(self):
        """
        🔍 Get current behavior for stack_info parameter
        
        Returns:
            dict: Current stack_info behavior configuration
        """
        return {
            "config_enabled": self.call_stack_config.enabled,
            "honors_stack_info_param": True,  # Always true with new logic
            "stack_info_overrides_config": True,  # stack_info=True always shows stack
            "display_mode": self.call_stack_config.display_mode,
            "depth_when_forced": self.call_stack_config.depth if self.call_stack_config.depth > 0 else 5,
            "note": "stack_info=True will ALWAYS show stack trace, even if config disabled"
        }
    
    def test_stack_info_consistency(self):
        """
        🧪 Test and demonstrate stack_info parameter behavior
        """
        original_enabled = self.call_stack_config.enabled
        original_level = None
        
        # Find current console level
        for handler in self.logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                original_level = handler.level
                break
        
        try:
            # Test with config disabled
            self.configure_call_stack_tracing(enabled=False)
            self.set_console_level("DEBUG")
            
            self.logger.info("="*60)
            self.logger.info("🧪 STACK_INFO PARAMETER TEST")
            self.logger.info("="*60)
            
            self.logger.info("1️⃣ Config DISABLED, stack_info not specified:")
            self.logger.debug("   This should NOT show stack trace")
            
            self.logger.info("\n2️⃣ Config DISABLED, stack_info=True:")
            self.logger.debug("   This SHOULD show stack trace", stack_info=True)
            
            # Test with config enabled
            self.configure_call_stack_tracing(enabled=True, depth=3, display_mode='arrows')
            
            self.logger.info("\n3️⃣ Config ENABLED, stack_info not specified:")
            self.logger.debug("   This SHOULD show stack trace (auto)")
            
            self.logger.info("\n4️⃣ Config ENABLED, stack_info=True:")
            self.logger.debug("   This SHOULD show stack trace (explicit)", stack_info=True)
            
            self.logger.info("\n✅ Stack info parameter is working consistently!")
            self.logger.info("   - stack_info=True ALWAYS shows stack")
            self.info("   - Config only controls automatic stack tracing")
            
        finally:
            # Restore original settings
            self.configure_call_stack_tracing(enabled=original_enabled)
            if original_level:
                for handler in self.logger.handlers:
                    if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                        handler.setLevel(original_level)

# Create singleton instance
logger = SingletonLogger()

# ========================================
# 🎯 CONVENIENCE DECORATORS FOR FUNCTION TRACING
# ========================================

def trace_calls(show_params: bool = True, show_result: bool = True):
    """
    Decorator để automatically trace function calls
    
    Args:
        show_params: Show function parameters
        show_result: Show return value
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            
            # Log entry
            if show_params:
                params = {}
                if args: params['args'] = args
                if kwargs: params['kwargs'] = kwargs
                logger.trace_function_entry(func_name, **params)
            else:
                logger.trace_function_entry(func_name)
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # Log exit
                if show_result:
                    logger.trace_function_exit(func_name, result)
                else:
                    logger.trace_function_exit(func_name)
                
                return result
                
            except Exception as e:
                logger.error(f"❌ EXCEPTION in {func_name}: {str(e)}")
                raise
                
        return wrapper
    return decorator

def trace_async_calls(show_params: bool = True, show_result: bool = True):
    """
    Decorator để automatically trace async function calls
    
    Args:
        show_params: Show function parameters  
        show_result: Show return value
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            func_name = func.__name__
            
            # Log entry
            if show_params:
                params = {}
                if args: params['args'] = args
                if kwargs: params['kwargs'] = kwargs
                logger.trace_function_entry(func_name, **params)
            else:
                logger.trace_function_entry(func_name)
            
            try:
                # Execute async function
                result = await func(*args, **kwargs)
                
                # Log exit
                if show_result:
                    logger.trace_function_exit(func_name, result)
                else:
                    logger.trace_function_exit(func_name)
                
                return result
                
            except Exception as e:
                logger.error(f"❌ ASYNC EXCEPTION in {func_name}: {str(e)}")
                raise
                
        return wrapper
    return decorator

# ========================================
# 🔧 EXAMPLE USAGE & TESTING
# ========================================

if __name__ == "__main__":
    # Test call stack tracing
    print("🧪 Testing Call Stack Tracing...")
    
    # Enable call stack tracing
    logger.set_console_level("DEBUG")
    logger.enable_call_stack_trace(True, depth=3, show_immediate_caller=False)
    
    @trace_calls(show_params=True, show_result=True)
    def function_a(param1, param2):
        """Function A calls Function B"""
        logger.info("📝 Inside Function A")
        return function_b(param1 * 2)
    
    @trace_calls(show_params=True, show_result=True)
    def function_b(value):
        """Function B calls Function C"""
        logger.info("📝 Inside Function B")
        return function_c(value + 10)
    
    @trace_calls(show_params=True, show_result=True)
    def function_c(final_value):
        """Function C - final calculation"""
        logger.info("📝 Inside Function C - final calculation")
        result = final_value * 3
        logger.warning(f"⚠️  Important calculation result: {result}")
        return result
    
    # Test the call chain
    print("\n🚀 Starting test call chain...")
    result = function_a("hello", "world")
    print(f"\n✅ Final result: {result}")
    
    print("\n" + "="*60)
    print("🔍 Testing immediate caller mode...")
    
    # Test immediate caller mode
    logger.enable_call_stack_trace(True, depth=3, show_immediate_caller=True)
    
    def simple_function():
        logger.info("📝 This is a simple function")
        logger.debug("🔧 Debug message from simple function")
    
    def caller_function():
        logger.info("📝 About to call simple function")
        simple_function()
        logger.info("📝 Called simple function successfully")
    
    caller_function()
    
    print("\n✅ Call stack tracing test completed!") 