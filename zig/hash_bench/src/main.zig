const std = @import("std");
const keccak256 = @import("crypto/keccak256_accel.zig");
const clap = @import("clap");

var tid: u64 = 0;
var mutex = std.Thread.Mutex{};
var n: u64 = 0;
var b: u64 = 0;
var r: u64 = 0;
var v: u64 = 0;

pub fn main() !void {
    var output1: [32]u8 = undefined;

    keccak256.Keccak256_Accel.hash("", &output1);

    std.debug.print("test vector {x}\n", .{&output1});

    var gpa = std.heap.DebugAllocator(.{}){};
    defer _ = gpa.deinit();

    // First we specify what parameters our program can take.
    // We can use `parseParamsComptime` to parse a string into an array of `Param(Help)`.
    const params = comptime clap.parseParamsComptime(
        \\-h, --help             Display this help and exit.
        \\-n, --number <u64>   Number of trials.
        \\-b, --batch <u64>    Batch size.
        \\-r, --report <u64>   Report interval.
        \\-v, --verbosity <u64> Verbosity.
        \\-t, --thread <u64>   Number of threads.
    );

    // Initialize our diagnostics, which can be used for reporting useful errors.
    // This is optional. You can also pass `.{}` to `clap.parse` if you don't
    // care about the extra information `Diagnostic` provides.
    var diag = clap.Diagnostic{};
    var res = clap.parse(clap.Help, &params, clap.parsers.default, .{
        .diagnostic = &diag,
        .allocator = gpa.allocator(),
    }) catch |err| {
        // Report useful error and exit.
        try diag.reportToFile(.stderr(), err);
        return err;
    };
    defer res.deinit();

    n = res.args.number orelse 100000;
    b = res.args.batch orelse 100000;
    r = res.args.report orelse 1000000;
    v = res.args.verbosity orelse 3;
    const t = res.args.thread orelse 1;
    var gTimer = try std.time.Timer.start();

    const taskFn = struct {
        pub fn call(timer: *std.time.Timer) void {
            while (true) {
                var output: [32]u8 = undefined;

                mutex.lock();
                const ltid = tid;
                tid = tid + b;
                mutex.unlock();

                if (ltid >= n) {
                    break;
                }

                if (v >= 3 and ltid % r == 0) {
                    std.debug.print("used time {}ns, hps {}\n", .{ timer.read(), 1000_000_000 * ltid / timer.read() });
                }

                for (ltid..ltid + b) |j| {
                    var buf: [100]u8 = .{0} ** 100;

                    std.mem.writeInt(u64, buf[92..100], j, std.builtin.Endian.big);

                    // keccak256.Keccak256_Accel.hash(&buf, &output);
                    std.crypto.hash.sha3.Keccak256.hash(&buf, &output, .{});

                    if (v >= 5) {
                        std.debug.print("key: {}, hash: {x}\n", .{ j, &output });
                    }
                }
            }
        }
    };

    var threads = std.ArrayList(std.Thread){};
    for (0..t) {
        try threads.append(try std.Thread.spawn(.{}, taskFn.call, .{&gTimer}));
    }

    for (0..t) |i| {
        threads[i].join();
    }
    std.debug.print("used time {}ns, hps {}\n", .{ gTimer.read(), 1000_000_000 * n / gTimer.read() });
}
